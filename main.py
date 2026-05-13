from fastapi import FastAPI, Request, WebSocket, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import json
import asyncio
import websockets
import base64
import io
import httpx
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Union
from pydantic import BaseModel, model_validator
import numpy as np
from scipy import signal
import wave


# Azure Communication Services
from azure.communication.callautomation import (
    CallAutomationClient,
    PhoneNumberIdentifier,
    MediaStreamingOptions,
    StreamingTransportType,
    MediaStreamingContentType,
    MediaStreamingAudioChannelType,
    AudioFormat
)

# Funciones de DB2
from functions.functions import tools, available_functions, execute_function

load_dotenv()

# Configuracion
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PUBLIC_AUDIO_BASE_URL = os.getenv("PUBLIC_AUDIO_BASE_URL", "http://10.240.64.27:8000")

ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")
CALLBACK_URI = os.getenv("CALLBACK_URI")  # URL publica - usar ngrok para desarrollo
TENANT_ID = os.getenv("TENANT_ID")  # Microsoft 365 Tenant ID para llamadas a Teams

# Microsoft Graph API (para crear reuniones de Teams con link compartible)
GRAPH_CLIENT_ID = os.getenv("GRAPH_CLIENT_ID")
GRAPH_CLIENT_SECRET = os.getenv("GRAPH_CLIENT_SECRET")
MEETING_ORGANIZER_ID = os.getenv("MEETING_ORGANIZER_ID")  # Object ID del usuario organizador


# Cargar prompt
def load_prompt():
    try:
        with open('prompt.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Eres un asistente de voz amigable que habla espanol."


SYSTEM_PROMPT = load_prompt()

# Cliente de ACS (se inicializa si hay connection string)
acs_client: Optional[CallAutomationClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializar recursos al arrancar"""
    global acs_client

    print("\n" + "=" * 50)
    print("CONFIGURACION")
    print("=" * 50)

    if ACS_CONNECTION_STRING:
        acs_client = CallAutomationClient.from_connection_string(ACS_CONNECTION_STRING)
        print("[OK] ACS Client inicializado")
    else:
        print("[!!] ACS_CONNECTION_STRING no configurado")

    if CALLBACK_URI:
        print(f"[OK] Callback URI: {CALLBACK_URI}")
    else:
        print("[!!] CALLBACK_URI no configurado")
        print("     Para desarrollo local usa ngrok:")
        print("     1. Instala ngrok: https://ngrok.com/download")
        print("     2. Ejecuta: ngrok http 8000")
        print("     3. Copia la URL https y ponla en .env como CALLBACK_URI")

    if graph_configured():
        print(f"[OK] Graph API configurado (organizer: {MEETING_ORGANIZER_ID})")
    else:
        print("[!!] Graph API no configurado (generate_meeting_link no disponible)")
        print("     Necesitas: GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET, MEETING_ORGANIZER_ID")

    if OPENAI_API_KEY:
        print("[OK] OPENAI_API_KEY configurada")
    else:
        print("[!!] OPENAI_API_KEY no configurada")

    print(f"[OK] PUBLIC_AUDIO_BASE_URL: {PUBLIC_AUDIO_BASE_URL}")
    print("=" * 50 + "\n")

    yield
    print("Cerrando aplicacion...")


app = FastAPI(
    title="Optinoc BOCC Realtime",
    description="API para llamadas de voz con IA usando Azure Communication Services y OpenAI Realtime",
    lifespan=lifespan
)

# Almacen de llamadas activas
active_calls: dict = {}

# ============================================================================
# AUDIO FILES PARA DRACHTIO / FREESWITCH
# ============================================================================

AUDIO_DIR = "/tmp/opti-audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")


# ============================================================================
# DRACHTIO / 3CX INTEGRATION
# ============================================================================

class DrachtioIncomingCall(BaseModel):
    call_id: str
    from_number: Optional[str] = None
    to_number: Optional[str] = None


@app.post("/calls/drachtio/incoming")
async def drachtio_incoming_call(event: DrachtioIncomingCall):
    active_calls[event.call_id] = {
        "call_id": event.call_id,
        "status": "connected",
        "provider": "drachtio",
        "channel": "3cx_extension",
        "response_channel": "3cx_extension",
        "targets": [event.to_number] if event.to_number else [],
        "from_number": event.from_number,
        "to_number": event.to_number,
        "started_at": datetime.now().isoformat(),
        "openai_ws": None,
        "media_ws": None,
        "bot_muted": False,
        "user_speaking": False,
        "whisper_buffer": b"",
        "first_message": "Saluda al usuario brevemente",
        "join_url": None
    }

    print(f"[DRACHTIO] Llamada registrada: {event.call_id}")
    print(f"[DRACHTIO] From: {event.from_number}")
    print(f"[DRACHTIO] To: {event.to_number}")

    return {
        "status": "ok",
        "call_id": event.call_id,
        "message": "Llamada registrada en FastAPI"
    }


class DrachtioGreetingRequest(BaseModel):
    call_id: str
    from_number: Optional[str] = None
    to_number: Optional[str] = None


def safe_filename(value: str) -> str:
    return "".join(
        c if c.isalnum() or c in ("-", "_") else "_"
        for c in value
    )


def pcm_bytes_to_wav_bytes(pcm_data: bytes, sample_rate: int = 16000) -> bytes:
    """
    Convierte PCM 16-bit mono a WAV.
    FreeSWITCH reproduce mejor un WAV con header correcto.
    """
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)

    wav_buffer.seek(0)
    return wav_buffer.read()


async def generate_realtime_audio_wav(prompt_text: str, output_path: str) -> str:
    """
    Usa la misma lógica de OpenAI Realtime del bot para generar audio.
    Genera un WAV local que luego FreeSWITCH puede reproducir.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY no está configurada")

    url = "wss://api.openai.com/v1/realtime?model=gpt-realtime-mini-2025-12-15"

    audio_chunks_24khz: list[bytes] = []
    final_transcript = ""

    async with websockets.connect(
        url,
        additional_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        },
        ping_interval=20,
        ping_timeout=10,
        close_timeout=10
    ) as ws:
        await ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": SYSTEM_PROMPT,
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "tools": tools,
                "temperature": 0.8
            }
        }))

        await ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt_text
                    }
                ]
            }
        }))

        await ws.send(json.dumps({"type": "response.create"}))

        async for message in ws:
            event = json.loads(message)
            event_type = event.get("type")

            if event_type == "response.audio.delta":
                audio_b64 = event.get("delta", "")
                if audio_b64:
                    audio_chunks_24khz.append(base64.b64decode(audio_b64))

            elif event_type == "response.audio_transcript.done":
                final_transcript = event.get("transcript", "")

            elif event_type == "response.done":
                break

            elif event_type == "error":
                print(f"[Realtime Greeting] Error: {event.get('error')}")
                break

    raw_audio_24khz = b"".join(audio_chunks_24khz)

    if not raw_audio_24khz:
        raise RuntimeError("OpenAI Realtime no generó audio")

    raw_b64_24khz = base64.b64encode(raw_audio_24khz).decode("utf-8")
    raw_b64_16khz = resample_audio(raw_b64_24khz, input_rate=24000, output_rate=16000)
    raw_audio_16khz = base64.b64decode(raw_b64_16khz)

    wav_data = pcm_bytes_to_wav_bytes(raw_audio_16khz, sample_rate=16000)

    with open(output_path, "wb") as f:
        f.write(wav_data)

    return final_transcript


@app.post("/bot/drachtio/realtime-greeting")
async def drachtio_realtime_greeting(request: DrachtioGreetingRequest):
    """
    Genera un saludo usando la misma IA Realtime del bot.
    Devuelve una URL WAV para que FreeSWITCH la reproduzca.
    """
    safe_call_id = safe_filename(request.call_id)

    audio_filename = f"greeting_{safe_call_id}.wav"
    audio_path = os.path.join(AUDIO_DIR, audio_filename)

    prompt_text = (
        "Genera un saludo breve de voz para una llamada telefónica. "
        "Preséntate como OPTI, asistente virtual de Optimize IT, "
        "di que ya estás conectado por 3CX y pregunta en qué puedes ayudar. "
        "No menciones detalles técnicos."
    )

    try:
        transcript = await generate_realtime_audio_wav(prompt_text, audio_path)

        audio_url = f"{PUBLIC_AUDIO_BASE_URL}/audio/{audio_filename}"

        print(f"[DRACHTIO][AI] Saludo generado para {request.call_id}")
        print(f"[DRACHTIO][AI] Texto: {transcript}")
        print(f"[DRACHTIO][AI] Audio: {audio_url}")

        return {
            "status": "ok",
            "call_id": request.call_id,
            "text": transcript,
            "audio_url": audio_url
        }

    except Exception as e:
        print(f"[DRACHTIO][AI] Error generando saludo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def transcribe_uploaded_audio_with_whisper(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """
    Transcribe un archivo de audio recibido desde FreeSWITCH.
    A diferencia de transcribe_with_whisper(), aquí el audio ya viene como WAV/archivo.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY no está configurada")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                },
                files={
                    "file": (filename or "audio.wav", audio_bytes, "audio/wav")
                },
                data={
                    "model": "whisper-1",
                    "language": "es"
                },
                timeout=30.0
            )

        if response.status_code != 200:
            print(f"[DRACHTIO][Whisper] Error API: {response.status_code} - {response.text}")
            raise RuntimeError(response.text)

        result = response.json()
        transcript = result.get("text", "").strip()

        print(f"[DRACHTIO][Whisper] Transcripción: {transcript}")
        return transcript

    except Exception as e:
        print(f"[DRACHTIO][Whisper] Error transcribiendo audio: {e}")
        raise


async def generate_drachtio_turn_audio_wav(
    call_id: str,
    user_text: str,
    output_path: str,
    from_number: Optional[str] = None,
    to_number: Optional[str] = None
) -> str:
    """
    Genera una respuesta hablada para 3CX usando OpenAI Realtime + tools DB2.
    Si el modelo solicita una función, se ejecuta execute_function() y se continúa la respuesta.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY no está configurada")

    url = "wss://api.openai.com/v1/realtime?model=gpt-realtime-mini-2025-12-15"

    audio_chunks_24khz: list[bytes] = []
    final_transcript = ""

    channel_instruction = (
        "Contexto de canal: esta conversación viene desde una extensión telefónica 3CX "
        "a través de Drachtio y FreeSWITCH. "
        "Responde SIEMPRE para ser escuchado por voz en la misma llamada. "
        "No digas que enviarás la respuesta por Teams, correo, chat ni otro canal. "
        "Sé claro, breve y natural. Si consultas DB2 o herramientas, resume el resultado para voz."
    )

    user_prompt = (
        f"{channel_instruction}\n\n"
        f"Call ID: {call_id}\n"
        f"From: {from_number or ''}\n"
        f"To: {to_number or ''}\n\n"
        f"Pregunta del usuario transcrita desde la llamada 3CX:\n{user_text}"
    )

    pending_function_response = False

    async with websockets.connect(
        url,
        additional_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        },
        ping_interval=20,
        ping_timeout=10,
        close_timeout=10
    ) as ws:
        await ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": SYSTEM_PROMPT + "\n\n" + channel_instruction,
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "tools": tools,
                "temperature": 0.7
            }
        }))

        await ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": user_prompt
                    }
                ]
            }
        }))

        await ws.send(json.dumps({"type": "response.create"}))

        async for message in ws:
            event = json.loads(message)
            event_type = event.get("type")

            if event_type == "response.audio.delta":
                audio_b64 = event.get("delta", "")
                if audio_b64:
                    audio_chunks_24khz.append(base64.b64decode(audio_b64))

            elif event_type == "response.audio_transcript.done":
                transcript = event.get("transcript", "").strip()
                if transcript:
                    final_transcript = transcript
                    print(f"[DRACHTIO][AI] Respuesta texto: {final_transcript}")

            elif event_type == "response.output_item.added":
                item = event.get("item", {})
                if item.get("type") == "function_call":
                    print(f"[DRACHTIO][AI] Function call agregado: {item.get('name')}")

            elif event_type == "response.function_call_arguments.done":
                function_name = event.get("name")
                function_args_str = event.get("arguments", "{}")
                function_call_id = event.get("call_id")

                print(f"[DRACHTIO][AI] Function call: {function_name}")
                print(f"[DRACHTIO][AI] Arguments: {function_args_str}")

                try:
                    function_args = json.loads(function_args_str) if function_args_str else {}

                    if function_name == "set_bot_muted":
                        muted = function_args.get("muted", False)
                        if call_id in active_calls:
                            active_calls[call_id]["bot_muted"] = muted

                        function_result = json.dumps({
                            "success": True,
                            "muted": muted,
                            "message": "Estado de silencio actualizado para esta llamada 3CX."
                        })
                    else:
                        function_result = execute_function(function_name, function_args)

                    print(f"[DRACHTIO][AI] Resultado función: {str(function_result)[:300]}...")

                    await ws.send(json.dumps({
                        "type": "conversation.item.create",
                        "item": {
                            "type": "function_call_output",
                            "call_id": function_call_id,
                            "output": function_result
                        }
                    }))

                    pending_function_response = True
                    await ws.send(json.dumps({"type": "response.create"}))

                except Exception as e:
                    print(f"[DRACHTIO][AI] Error ejecutando función: {e}")

                    await ws.send(json.dumps({
                        "type": "conversation.item.create",
                        "item": {
                            "type": "function_call_output",
                            "call_id": function_call_id,
                            "output": json.dumps({"error": str(e)})
                        }
                    }))

                    pending_function_response = True
                    await ws.send(json.dumps({"type": "response.create"}))

            elif event_type == "response.done":
                if pending_function_response:
                    pending_function_response = False
                    continue
                break

            elif event_type == "error":
                print(f"[DRACHTIO][AI] Error event: {event.get('error')}")
                break

    raw_audio_24khz = b"".join(audio_chunks_24khz)

    if not raw_audio_24khz:
        raise RuntimeError("OpenAI Realtime no generó audio de respuesta")

    raw_b64_24khz = base64.b64encode(raw_audio_24khz).decode("utf-8")
    raw_b64_16khz = resample_audio(raw_b64_24khz, input_rate=24000, output_rate=16000)
    raw_audio_16khz = base64.b64decode(raw_b64_16khz)

    wav_data = pcm_bytes_to_wav_bytes(raw_audio_16khz, sample_rate=16000)

    with open(output_path, "wb") as f:
        f.write(wav_data)

    return final_transcript


@app.post("/bot/drachtio/audio-turn")
async def drachtio_audio_turn(
    call_id: str = Form(...),
    from_number: Optional[str] = Form(None),
    to_number: Optional[str] = Form(None),
    audio: UploadFile = File(...)
):
    """
    Recibe una grabación WAV desde FreeSWITCH/Node, transcribe la pregunta,
    consulta la IA con herramientas DB2 y devuelve un WAV para reproducir por 3CX.
    """
    if call_id not in active_calls:
        active_calls[call_id] = {
            "call_id": call_id,
            "status": "connected",
            "provider": "drachtio",
            "channel": "3cx_extension",
            "response_channel": "3cx_extension",
            "targets": [to_number] if to_number else [],
            "from_number": from_number,
            "to_number": to_number,
            "started_at": datetime.now().isoformat(),
            "openai_ws": None,
            "media_ws": None,
            "bot_muted": False,
            "user_speaking": False,
            "whisper_buffer": b"",
            "first_message": None,
            "join_url": None
        }
    else:
        active_calls[call_id]["provider"] = "drachtio"
        active_calls[call_id]["channel"] = "3cx_extension"
        active_calls[call_id]["response_channel"] = "3cx_extension"
        active_calls[call_id]["from_number"] = from_number
        active_calls[call_id]["to_number"] = to_number

    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio vacío")

    try:
        user_text = await transcribe_uploaded_audio_with_whisper(
            audio_bytes=audio_bytes,
            filename=audio.filename or "turn.wav"
        )

        if not user_text:
            return {
                "status": "no_speech",
                "call_id": call_id,
                "transcript": "",
                "response_text": "",
                "audio_url": None,
                "message": "No se detectó voz en la grabación"
            }

        safe_call_id = safe_filename(call_id)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")

        audio_filename = f"response_{safe_call_id}_{timestamp}.wav"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)

        response_text = await generate_drachtio_turn_audio_wav(
            call_id=call_id,
            user_text=user_text,
            output_path=audio_path,
            from_number=from_number,
            to_number=to_number
        )

        audio_url = f"{PUBLIC_AUDIO_BASE_URL}/audio/{audio_filename}"

        active_calls[call_id]["last_user_text"] = user_text
        active_calls[call_id]["last_response_text"] = response_text
        active_calls[call_id]["last_response_audio_url"] = audio_url
        active_calls[call_id]["updated_at"] = datetime.now().isoformat()

        print(f"[DRACHTIO][TURN] Call: {call_id}")
        print(f"[DRACHTIO][TURN] Usuario: {user_text}")
        print(f"[DRACHTIO][TURN] Respuesta: {response_text}")
        print(f"[DRACHTIO][TURN] Audio: {audio_url}")

        return {
            "status": "ok",
            "call_id": call_id,
            "provider": "drachtio",
            "channel": "3cx_extension",
            "response_channel": "3cx_extension",
            "transcript": user_text,
            "response_text": response_text,
            "audio_url": audio_url
        }

    except Exception as e:
        print(f"[DRACHTIO][TURN] Error procesando turno: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ============================================================================
# TOOLS EXECUTION API PARA NODE REALTIME BRIDGE
# ============================================================================

class ToolExecuteRequest(BaseModel):
    function_name: str
    function_args: Optional[dict] = None
    call_id: Optional[str] = None
    channel: Optional[str] = None


@app.get("/bot/tools")
async def list_bot_tools():
    """
    Lista las herramientas disponibles para OpenAI Realtime.
    Node realtime-bridge.js usa este endpoint para configurar la sesión con tools.
    """
    return {
        "status": "ok",
        "tools": tools,
        "available_functions": list(available_functions.keys())
    }


@app.post("/bot/tools/execute")
async def execute_bot_tool(request: ToolExecuteRequest):
    """
    Ejecuta una función del bot, por ejemplo consultas DB2.
    Este endpoint lo usa realtime-bridge.js cuando OpenAI Realtime solicita function_call.
    """
    try:
        print("[TOOLS] Function call desde realtime bridge")
        print(f"[TOOLS] call_id: {request.call_id}")
        print(f"[TOOLS] channel: {request.channel}")
        print(f"[TOOLS] function_name: {request.function_name}")
        print(f"[TOOLS] function_args: {request.function_args}")

        if request.function_name == "set_bot_muted":
            muted = False
            if request.function_args:
                muted = bool(request.function_args.get("muted", False))

            if request.call_id and request.call_id in active_calls:
                active_calls[request.call_id]["bot_muted"] = muted

            result = json.dumps({
                "success": True,
                "muted": muted,
                "message": "Estado de silencio actualizado para esta llamada 3CX."
            }, ensure_ascii=False)

        else:
            result = execute_function(
                request.function_name,
                request.function_args or {}
            )

        print(f"[TOOLS] Resultado: {str(result)[:500]}...")

        return {
            "status": "ok",
            "function_name": request.function_name,
            "result": result
        }

    except Exception as e:
        print(f"[TOOLS] Error ejecutando herramienta: {e}")
        return {
            "status": "error",
            "function_name": request.function_name,
            "error": str(e)
        }


# ============================================================================
# MICROSOFT GRAPH API (Reuniones de Teams)
# ============================================================================

_graph_token_cache: dict = {"access_token": None, "expires_at": 0}


def graph_configured() -> bool:
    return all([GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET, TENANT_ID, MEETING_ORGANIZER_ID])


async def get_graph_token() -> str:
    """Obtiene un access token de Microsoft Graph via client credentials flow."""
    now = datetime.now(timezone.utc).timestamp()
    if _graph_token_cache["access_token"] and _graph_token_cache["expires_at"] > now + 60:
        return _graph_token_cache["access_token"]

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": GRAPH_CLIENT_ID,
                "client_secret": GRAPH_CLIENT_SECRET,
                "scope": "https://graph.microsoft.com/.default",
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()

    _graph_token_cache["access_token"] = data["access_token"]
    _graph_token_cache["expires_at"] = now + data.get("expires_in", 3600)
    return data["access_token"]


async def create_teams_meeting(subject: str = "OPTI - Llamada NOC") -> dict:
    """
    Crea una Online Meeting en Teams via Microsoft Graph API.

    Requiere App Registration con permiso OnlineMeetings.ReadWrite.All (application).

    Returns:
        dict con joinWebUrl, meetingId, subject, etc.
    """
    token = await get_graph_token()

    now = datetime.now(timezone.utc)
    body = {
        "subject": subject,
        "startDateTime": now.isoformat(),
        "endDateTime": (now + timedelta(hours=1)).isoformat(),
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://graph.microsoft.com/v1.0/users/{MEETING_ORGANIZER_ID}/onlineMeetings",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=15.0,
        )
        resp.raise_for_status()
        meeting = resp.json()

    print(f"[Graph] Reunión creada: {meeting.get('joinWebUrl', '')[:80]}...")
    return meeting


# ============================================================================
# MODELOS
# ============================================================================

class OutboundCallRequest(BaseModel):
    """Solicitud para hacer una llamada saliente.

    Acepta un solo destino (target_number) o múltiples (target_numbers) para llamadas grupales.
    """
    target_number: Optional[str] = None
    target_numbers: Optional[List[str]] = None
    target_type: str = "phone"  # "phone" o "teams"
    display_name: str = "Optinoc VoiceBot"
    first_message: Optional[str] = None
    generate_meeting_link: bool = False
    meeting_subject: Optional[str] = None

    @model_validator(mode="after")
    def validate_targets(self):
        if not self.target_number and not self.target_numbers:
            raise ValueError("Debes proporcionar target_number o target_numbers")
        if self.target_number and self.target_numbers:
            raise ValueError("Usa target_number (un destino) o target_numbers (varios), no ambos")
        return self

    @property
    def all_targets(self) -> List[str]:
        """Retorna la lista unificada de destinos."""
        if self.target_numbers:
            return self.target_numbers
        return [self.target_number]


class CallInfo(BaseModel):
    """Informacion de una llamada"""
    call_id: str
    status: str
    targets: List[str]
    started_at: str
    join_url: Optional[str] = None


# ============================================================================
# ENDPOINTS PRINCIPALES
# ============================================================================

@app.get("/")
async def root():
    return {
        "status": "VoiceBot API Running",
        "acs_configured": acs_client is not None,
        "active_calls": len(active_calls)
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/test/websocket")
async def test_websocket():
    """Verifica que el WebSocket de media esté accesible"""
    return {
        "websocket_url": f"{CALLBACK_URI}/ws/media",
        "callback_url": f"{CALLBACK_URI}/callbacks/acs",
        "note": "Verifica que estas URLs sean accesibles desde internet"
    }


# ============================================================================
# LLAMADAS SALIENTES
# ============================================================================

@app.post("/calls/outbound", response_model=CallInfo)
async def make_outbound_call(request: OutboundCallRequest):
    """
    Inicia una llamada saliente a uno o varios destinos.

    - Un destino:   {"target_number": "GUID-object-id", "target_type": "teams"}
    - Varios (grupal): {"target_numbers": ["GUID-1", "GUID-2"], "target_type": "teams"}
    - Telefono:     {"target_number": "+573001234567", "target_type": "phone"}

    En llamadas grupales de Teams, todos los participantes reciben la llamada
    y se unen a la misma sesión con OPTI.
    """
    if not acs_client:
        raise HTTPException(status_code=503, detail="ACS no configurado. Configura ACS_CONNECTION_STRING en .env")

    if not CALLBACK_URI:
        raise HTTPException(
            status_code=503,
            detail="CALLBACK_URI no configurado. Usa ngrok y configura la URL en .env"
        )

    try:
        targets = request.all_targets
        participants = []
        join_url: Optional[str] = None

        if request.generate_meeting_link:
            if not graph_configured():
                raise HTTPException(
                    status_code=503,
                    detail="Graph API no configurado. Necesitas GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET, TENANT_ID y MEETING_ORGANIZER_ID en .env"
                )
            subject = request.meeting_subject or "OPTI - Llamada NOC"
            meeting = await create_teams_meeting(subject=subject)
            join_url = meeting.get("joinWebUrl")
            print(f"[CALL] Meeting link generado: {join_url}")

        if request.target_type == "teams":
            from azure.communication.callautomation import MicrosoftTeamsUserIdentifier, CommunicationCloudEnvironment

            if not TENANT_ID:
                raise HTTPException(
                    status_code=503,
                    detail="TENANT_ID no configurado en .env. Necesario para llamadas a Teams"
                )

            for t in targets:
                if "@" in t and "." in t:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Usa el Object ID (GUID), no el email/UPN: {t}"
                    )
                print(f"[CALL] Participante Teams: {t}")
                participants.append(
                    MicrosoftTeamsUserIdentifier(
                        user_id=t,
                        cloud=CommunicationCloudEnvironment.PUBLIC
                    )
                )
        else:
            for t in targets:
                participants.append(PhoneNumberIdentifier(t))

        print(f"[CALL] Tenant ID: {TENANT_ID}")
        print(f"[CALL] Total participantes: {len(participants)}")

        websocket_url = CALLBACK_URI.replace("https://", "wss://").replace("http://", "ws://")
        media_streaming = MediaStreamingOptions(
            transport_url=f"{websocket_url}/ws/media",
            transport_type=StreamingTransportType.WEBSOCKET,
            content_type=MediaStreamingContentType.AUDIO,
            audio_channel_type=MediaStreamingAudioChannelType.MIXED,
            start_media_streaming=True,
            enable_bidirectional=True,
            audio_format=AudioFormat.PCM16_K_MONO
        )

        print(f"[CALL] WebSocket URL: {websocket_url}/ws/media")
        print(f"[CALL] Bidirectional audio: ENABLED")

        call_result = acs_client.create_call(
            target_participant=participants if len(participants) > 1 else participants[0],
            callback_url=f"{CALLBACK_URI}/callbacks/acs",
            media_streaming=media_streaming,
            source_display_name=request.display_name
        )

        call_id = call_result.call_connection_id

        active_calls[call_id] = {
            "call_id": call_id,
            "status": "connecting",
            "targets": targets,
            "target_type": request.target_type,
            "target_participants": participants,
            "started_at": datetime.now().isoformat(),
            "openai_ws": None,
            "bot_muted": False,
            "user_speaking": False,
            "whisper_buffer": b"",
            "first_message": request.first_message,
            "join_url": join_url
        }

        print(f"[CALL] Llamada iniciada: {call_id} -> {targets}")

        return CallInfo(
            call_id=call_id,
            status="connecting",
            targets=targets,
            started_at=active_calls[call_id]["started_at"],
            join_url=join_url
        )

    except Exception as e:
        print(f"[CALL] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/calls")
async def list_calls():
    """Lista todas las llamadas activas"""
    return {
        "total": len(active_calls),
        "calls": [
            {
                "call_id": call_id,
                "status": info.get("status"),
                "provider": info.get("provider", "acs"),
                "channel": info.get("channel"),
                "response_channel": info.get("response_channel"),
                "targets": info.get("targets", []),
                "from_number": info.get("from_number"),
                "to_number": info.get("to_number"),
                "started_at": info.get("started_at"),
                "updated_at": info.get("updated_at"),
                "last_user_text": info.get("last_user_text"),
                "last_response_text": info.get("last_response_text"),
                "last_response_audio_url": info.get("last_response_audio_url"),
                "join_url": info.get("join_url")
            }
            for call_id, info in active_calls.items()
        ]
    }


@app.delete("/calls/{call_id}")
async def hangup_call(call_id: str):
    """Termina una llamada"""
    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Llamada no encontrada")

    if not acs_client:
        raise HTTPException(status_code=503, detail="ACS no configurado")

    try:
        call_connection = acs_client.get_call_connection(call_id)
        call_connection.hang_up(is_for_everyone=True)

        if call_id in active_calls:
            del active_calls[call_id]

        return {"status": "call_ended", "call_id": call_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEBHOOKS DE ACS (Callbacks)
# ============================================================================

@app.post("/callbacks/acs")
async def acs_callback(request: Request):
    """
    Recibe eventos de Azure Communication Services.
    """
    try:
        events = await request.json()

        if not isinstance(events, list):
            events = [events]

        for event in events:
            event_type = event.get("type", "")
            call_id = event.get("data", {}).get("callConnectionId", "")

            print(f"[ACS Event] {event_type} - Call: {call_id}")

            if event_type == "Microsoft.Communication.CreateCallFailed":
                data = event.get("data", {})
                result_info = data.get("resultInformation", {})
                print(f"[ACS ERROR] CreateCallFailed:")
                print(f"  - Code: {result_info.get('code', 'N/A')}")
                print(f"  - SubCode: {result_info.get('subCode', 'N/A')}")
                print(f"  - Message: {result_info.get('message', 'Sin mensaje')}")
                print(f"  - Full data: {json.dumps(data, indent=2)}")

            if event_type == "Microsoft.Communication.CallConnected":
                if call_id in active_calls:
                    active_calls[call_id]["status"] = "connected"
                    asyncio.create_task(connect_to_openai_realtime(call_id))

            elif event_type == "Microsoft.Communication.CallDisconnected":
                data = event.get("data", {})
                result_info = data.get("resultInformation", {})
                if result_info:
                    print(
                        f"[ACS] CallDisconnected reason: "
                        f"Code={result_info.get('code')}, "
                        f"SubCode={result_info.get('subCode')}, "
                        f"Message={result_info.get('message')}"
                    )

                if call_id in active_calls:
                    openai_ws = active_calls[call_id].get("openai_ws")
                    if openai_ws:
                        await openai_ws.close()
                    del active_calls[call_id]

            elif event_type == "Microsoft.Communication.MediaStreamingStarted":
                print(f"[ACS] Media streaming iniciado para {call_id}")

            elif event_type == "Microsoft.Communication.MediaStreamingStopped":
                print(f"[ACS] Media streaming detenido para {call_id}")

            elif event_type == "Microsoft.Communication.MediaStreamingFailed":
                data = event.get("data", {})
                result_info = data.get("resultInformation", {})
                print(f"[ACS ERROR] MediaStreamingFailed:")
                print(f"  - Code: {result_info.get('code', 'N/A')}")
                print(f"  - SubCode: {result_info.get('subCode', 'N/A')}")
                print(f"  - Message: {result_info.get('message', 'Sin mensaje')}")
                print(f"  - WebSocket URL esperada: {CALLBACK_URI}/ws/media")
                print(f"  - Full data: {json.dumps(data, indent=2)}")

        return {"status": "ok"}

    except Exception as e:
        print(f"Error procesando callback ACS: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# ============================================================================
# WEBSOCKET PARA MEDIA STREAMING (Audio de ACS)
# ============================================================================

@app.websocket("/ws/media")
async def media_websocket(websocket: WebSocket):
    """
    WebSocket que recibe el audio de ACS y lo envia a OpenAI Realtime.
    """
    print(f"[Media WS] Intentando aceptar conexion...")
    print(f"[Media WS] Headers: {websocket.headers}")
    print(f"[Media WS] Client: {websocket.client}")

    await websocket.accept()
    print("[Media WS] Conexion aceptada de ACS")

    call_id = websocket.headers.get("x-ms-call-connection-id")
    print(f"[Media WS] Call ID desde headers: {call_id}")

    if call_id and call_id in active_calls:
        active_calls[call_id]["media_ws"] = websocket
        print(f"[Media WS] ✅ WebSocket guardado para {call_id} (desde headers)")
    elif call_id:
        print(f"[Media WS] ⚠️ Call ID {call_id} no encontrado en active_calls aún")
    else:
        print(f"[Media WS] ⚠️ No se encontró x-ms-call-connection-id en headers")

    try:
        async for message in websocket.iter_text():
            data = json.loads(message)

            if "kind" in data:
                if data["kind"] == "AudioMetadata":
                    print(f"[Media WS] AudioMetadata recibido")

                    if call_id and call_id in active_calls and not active_calls[call_id].get("media_ws"):
                        active_calls[call_id]["media_ws"] = websocket
                        print(f"[Media WS] ✅ WebSocket guardado para {call_id} (desde AudioMetadata)")

                elif data["kind"] == "AudioData":
                    audio_data = data.get("audioData", {}).get("data", "")

                    if call_id and call_id in active_calls and audio_data:
                        bot_muted = active_calls[call_id].get("bot_muted", False)

                        if bot_muted:
                            await add_audio_to_whisper_buffer(call_id, audio_data)
                        else:
                            openai_ws = active_calls[call_id].get("openai_ws")

                            if openai_ws:
                                audio_24khz = resample_audio(
                                    audio_data,
                                    input_rate=16000,
                                    output_rate=24000
                                )

                                await openai_ws.send(json.dumps({
                                    "type": "input_audio_buffer.append",
                                    "audio": audio_24khz
                                }))
                            else:
                                await asyncio.sleep(0.1)

    except Exception as e:
        print(f"[Media WS] Error: {e}")
    finally:
        if call_id and call_id in active_calls:
            active_calls[call_id]["media_ws"] = None
        print(f"[Media WS] Desconectado: {call_id}")


# ============================================================================
# CONEXION CON OPENAI REALTIME
# ============================================================================

async def connect_to_openai_realtime(call_id: str, retry_count: int = 0):
    """
    Establece conexion WebSocket con OpenAI Realtime API
    y maneja el flujo de audio bidireccional con reconexión automática.
    """
    MAX_RETRIES = 3

    if call_id not in active_calls:
        print(f"[OpenAI] Call {call_id} ya no existe en active_calls")
        return

    if retry_count >= MAX_RETRIES:
        print(f"[OpenAI] ❌ Máximo de reintentos alcanzado ({MAX_RETRIES}) para {call_id}")
        return

    if retry_count > 0:
        print(f"[OpenAI] 🔄 Reintento {retry_count}/{MAX_RETRIES} para {call_id}")

    if not OPENAI_API_KEY:
        print("[OpenAI] ❌ OPENAI_API_KEY no configurada")
        return

    url = "wss://api.openai.com/v1/realtime?model=gpt-realtime-mini-2025-12-15"

    try:
        async with websockets.connect(
            url,
            additional_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            },
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10
        ) as ws:
            active_calls[call_id]["openai_ws"] = ws
            print(f"[OpenAI] Conectado para llamada: {call_id}")

            await ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": SYSTEM_PROMPT,
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {"model": "whisper-1"},
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500
                    },
                    "tools": tools,
                    "temperature": 0.8
                }
            }))

            if retry_count == 0:
                first_msg = active_calls[call_id].get("first_message")
                prompt_text = first_msg if first_msg else "Saluda al usuario brevemente"
                print(f"[OpenAI] First message: {prompt_text}")

                await asyncio.sleep(2.0)
                await ws.send(json.dumps({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt_text}]
                    }
                }))
                await ws.send(json.dumps({"type": "response.create"}))
            else:
                print(f"[OpenAI] Reconexión exitosa, continuando conversación...")

            async for message in ws:
                if call_id not in active_calls:
                    break

                event = json.loads(message)
                event_type = event.get("type")

                if event_type == "response.audio.delta":
                    audio_b64 = event.get("delta", "")
                    if audio_b64:
                        await send_audio_to_acs(call_id, audio_b64)

                elif event_type == "response.audio_transcript.done":
                    transcript = event.get("transcript", "")
                    if transcript:
                        print(f"[OpenAI] 📝 Dijo: {transcript}")

                elif event_type == "response.done":
                    print(f"[OpenAI] Respuesta completada para {call_id}")

                elif event_type == "response.output_item.added":
                    item = event.get("item", {})
                    if item.get("type") == "function_call":
                        print(f"[OpenAI] 🔧 Function call agregado: {item.get('name')}")

                elif event_type == "response.output_item.done":
                    item = event.get("item", {})
                    if item.get("type") == "function_call":
                        print(f"[OpenAI] 🔧 Function call completado: {item.get('name')}")

                elif event_type == "response.function_call_arguments.done":
                    function_name = event.get("name")
                    function_args_str = event.get("arguments", "{}")
                    function_call_id = event.get("call_id")

                    print(f"[OpenAI] Function call: {function_name}")
                    print(f"[OpenAI] Call ID: {function_call_id}")
                    print(f"[OpenAI] Arguments: {function_args_str}")

                    try:
                        function_args = json.loads(function_args_str) if function_args_str else {}

                        if function_name == "set_bot_muted":
                            muted = function_args.get("muted", False)
                            active_calls[call_id]["bot_muted"] = muted

                            function_result = json.dumps({
                                "success": True,
                                "muted": muted,
                                "message": "Estado de silencio actualizado."
                            })
                        else:
                            function_result = execute_function(function_name, function_args)

                        print(f"[OpenAI] Resultado de función: {str(function_result)[:200]}...")

                        await ws.send(json.dumps({
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": function_call_id,
                                "output": function_result
                            }
                        }))

                        print(f"[OpenAI] ✅ Resultado enviado para call_id: {function_call_id}")

                        await ws.send(json.dumps({"type": "response.create"}))

                    except Exception as e:
                        print(f"[OpenAI] Error ejecutando función: {str(e)}")

                        await ws.send(json.dumps({
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": function_call_id,
                                "output": json.dumps({"error": str(e)})
                            }
                        }))
                        await ws.send(json.dumps({"type": "response.create"}))

                elif event_type == "input_audio_buffer.speech_started":
                    print(f"[OpenAI] 🎤 Usuario empezó a hablar - INTERRUPCIÓN")
                    active_calls[call_id]["user_speaking"] = True
                    await ws.send(json.dumps({"type": "response.cancel"}))
                    await stop_audio_in_acs(call_id)

                elif event_type == "input_audio_buffer.speech_stopped":
                    print(f"[OpenAI] 🎤 Usuario dejó de hablar")
                    active_calls[call_id]["user_speaking"] = False

                elif event_type == "error":
                    print(f"[OpenAI] ❌ Error event: {event.get('error')}")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"[OpenAI] ⚠️ WebSocket cerrado inesperadamente para {call_id}")
        print(f"[OpenAI] Código: {e.code}, Razón: {e.reason}")

        if call_id in active_calls and active_calls[call_id].get("status") == "connected":
            print(f"[OpenAI] 🔄 Intentando reconectar... (intento {retry_count + 1}/{MAX_RETRIES})")
            await asyncio.sleep(2)
            await connect_to_openai_realtime(call_id, retry_count + 1)
        else:
            print(f"[OpenAI] Llamada {call_id} ya terminó, no reconectar")

    except websockets.exceptions.WebSocketException as e:
        print(f"[OpenAI] ❌ Error de WebSocket: {type(e).__name__}: {e}")

        if call_id in active_calls and retry_count < MAX_RETRIES:
            print(f"[OpenAI] 🔄 Intentando reconectar... (intento {retry_count + 1}/{MAX_RETRIES})")
            await asyncio.sleep(2)
            await connect_to_openai_realtime(call_id, retry_count + 1)

    except asyncio.TimeoutError:
        print(f"[OpenAI] ⏱️ Timeout en la conexión para {call_id}")

        if call_id in active_calls and retry_count < MAX_RETRIES:
            print(f"[OpenAI] 🔄 Intentando reconectar... (intento {retry_count + 1}/{MAX_RETRIES})")
            await asyncio.sleep(2)
            await connect_to_openai_realtime(call_id, retry_count + 1)

    except Exception as e:
        print(f"[OpenAI] ❌ Error inesperado: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if call_id in active_calls:
            active_calls[call_id]["openai_ws"] = None
        print(f"[OpenAI] Desconectado para llamada: {call_id} (retry_count: {retry_count})")


# ============================================================================
# AUDIO PROCESSING
# ============================================================================

def resample_audio(audio_b64: str, input_rate: int = 24000, output_rate: int = 16000) -> str:
    """
    Resamplea audio PCM 16-bit de una tasa de muestreo a otra.
    """
    try:
        audio_bytes = base64.b64decode(audio_b64)
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        audio_float = audio_int16.astype(np.float32)

        num_samples = int(len(audio_float) * output_rate / input_rate)

        resampled = signal.resample(audio_float, num_samples)
        resampled_int16 = np.clip(resampled, -32768, 32767).astype(np.int16)

        resampled_bytes = resampled_int16.tobytes()
        resampled_b64 = base64.b64encode(resampled_bytes).decode('utf-8')

        return resampled_b64

    except Exception as e:
        print(f"[Audio] Error resampleando: {e}")
        return audio_b64


async def stop_audio_in_acs(call_id: str):
    """
    Envía comando para detener el audio actual en ACS.
    """
    if call_id not in active_calls:
        return

    media_ws = active_calls[call_id].get("media_ws")
    if not media_ws:
        return

    try:
        message = {
            "Kind": "StopAudio",
            "StopAudio": {},
            "AudioData": None
        }
        await media_ws.send_text(json.dumps(message))
        print(f"[Audio] ⏹️ StopAudio enviado a ACS para {call_id}")
    except Exception as e:
        print(f"[Audio] Error enviando StopAudio: {e}")


async def send_audio_to_acs(call_id: str, audio_b64: str):
    """
    Envia audio desde OpenAI a ACS a través del WebSocket de media.
    """
    if call_id not in active_calls:
        return

    if active_calls[call_id].get("bot_muted", False):
        return

    if active_calls[call_id].get("user_speaking", False):
        return

    media_ws = active_calls[call_id].get("media_ws")

    if not media_ws:
        return

    try:
        audio_16khz = resample_audio(audio_b64, input_rate=24000, output_rate=16000)

        message = {
            "Kind": "AudioData",
            "AudioData": {
                "Data": audio_16khz
            },
            "StopAudio": None
        }

        await media_ws.send_text(json.dumps(message))

    except Exception as e:
        print(f"[Audio] Error enviando a ACS: {e}")


# ============================================================================
# WHISPER API (Modo vigía - detección de palabra clave)
# ============================================================================

WHISPER_BUFFER_DURATION_SECONDS = 5
WHISPER_SAMPLE_RATE = 16000
WHISPER_BYTES_PER_SECOND = WHISPER_SAMPLE_RATE * 2
WHISPER_BUFFER_SIZE = WHISPER_BUFFER_DURATION_SECONDS * WHISPER_BYTES_PER_SECOND


def pcm_to_wav(pcm_data: bytes, sample_rate: int = 16000) -> bytes:
    """
    Convierte audio PCM raw a formato WAV para Whisper API.
    """
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    wav_buffer.seek(0)
    return wav_buffer.read()


async def transcribe_with_whisper(audio_bytes: bytes) -> str:
    """
    Envía audio a OpenAI Whisper API para transcripción.
    """
    try:
        wav_data = pcm_to_wav(audio_bytes)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                },
                files={
                    "file": ("audio.wav", wav_data, "audio/wav")
                },
                data={
                    "model": "whisper-1",
                    "language": "es"
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                transcript = result.get("text", "")
                if transcript:
                    print(f"[Whisper] 📝 Transcripción: {transcript}")
                return transcript
            else:
                print(f"[Whisper] ❌ Error API: {response.status_code} - {response.text}")
                return ""

    except Exception as e:
        print(f"[Whisper] ❌ Error: {e}")
        return ""


async def process_whisper_buffer(call_id: str):
    """
    Procesa el buffer de audio acumulado con Whisper y detecta la palabra clave OPTI.
    """
    if call_id not in active_calls:
        return

    call_data = active_calls[call_id]
    audio_buffer = call_data.get("whisper_buffer", b"")

    if len(audio_buffer) < WHISPER_BUFFER_SIZE:
        return

    buffer_to_process = audio_buffer[:WHISPER_BUFFER_SIZE]
    call_data["whisper_buffer"] = audio_buffer[WHISPER_BUFFER_SIZE:]

    transcript = await transcribe_with_whisper(buffer_to_process)

    if not transcript:
        return

    transcript_upper = transcript.upper()

    if "OPTI" in transcript_upper:
        print(f"[Whisper] 🎯 Palabra clave 'OPTI' detectada!")
        print(f"[Whisper] 📣 Reactivando bot para call {call_id}")

        call_data["bot_muted"] = False
        call_data["whisper_buffer"] = b""

        openai_ws = call_data.get("openai_ws")
        if openai_ws:
            try:
                await openai_ws.send(json.dumps({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": transcript}]
                    }
                }))
                await openai_ws.send(json.dumps({"type": "response.create"}))
                print(f"[Whisper] ✅ Contexto enviado a OpenAI Realtime")
            except Exception as e:
                print(f"[Whisper] ❌ Error enviando a OpenAI: {e}")


async def add_audio_to_whisper_buffer(call_id: str, audio_b64: str):
    """
    Agrega audio al buffer de Whisper para procesamiento en modo vigía.
    """
    if call_id not in active_calls:
        return

    try:
        audio_bytes = base64.b64decode(audio_b64)

        call_data = active_calls[call_id]
        if "whisper_buffer" not in call_data:
            call_data["whisper_buffer"] = b""

        call_data["whisper_buffer"] += audio_bytes

        if len(call_data["whisper_buffer"]) >= WHISPER_BUFFER_SIZE:
            await process_whisper_buffer(call_id)

    except Exception as e:
        print(f"[Whisper] Error agregando al buffer: {e}")


# ============================================================================
# UTILIDADES
# ============================================================================

def is_business_hours() -> bool:
    """
    Determina si estamos en horario laboral.
    Retorna True si es horario laboral (llamar por Teams).
    Retorna False si es fuera de horario (llamar por telefono).
    """
    now = datetime.now()

    if now.weekday() >= 5:
        return False

    if now.hour < 8 or now.hour >= 18:
        return False

    return True


@app.get("/utils/business-hours")
async def check_business_hours():
    """Verifica si estamos en horario laboral"""
    return {
        "is_business_hours": is_business_hours(),
        "current_time": datetime.now().isoformat(),
        "recommendation": "teams" if is_business_hours() else "phone"
    }


@app.get("/calls/{call_id}/mute-status")
async def get_mute_status(call_id: str):
    """Obtiene el estado de silenciamiento del bot en una llamada"""
    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Llamada no encontrada")

    is_muted = active_calls[call_id].get("bot_muted", False)
    return {
        "call_id": call_id,
        "bot_muted": is_muted,
        "status": "SILENCIADO" if is_muted else "ACTIVO",
        "instructions": {
            "mute": "Di: 'OPTI HAZ SILENCIO' o 'OPTI SILENCIO'",
            "unmute": "Di: 'OPTI VUELVE A HABLAR' o 'OPTI HABLA'"
        }
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
