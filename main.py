from fastapi import FastAPI, Request, WebSocket, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import json
import asyncio
import websockets
import base64
import io
import httpx
from dotenv import load_dotenv
from datetime import datetime
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
ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")
CALLBACK_URI = os.getenv("CALLBACK_URI")  # URL publica - usar ngrok para desarrollo
TENANT_ID = os.getenv("TENANT_ID")  # Microsoft 365 Tenant ID para llamadas a Teams

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
    
    print("\n" + "="*50)
    print("CONFIGURACION")
    print("="*50)
    
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
    
    print("="*50 + "\n")
    
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

        # ACS create_call acepta una lista de participantes para llamadas grupales
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
            "first_message": request.first_message
        }
        
        print(f"[CALL] Llamada iniciada: {call_id} -> {targets}")
        
        return CallInfo(
            call_id=call_id,
            status="connecting",
            targets=targets,
            started_at=active_calls[call_id]["started_at"]
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
                "status": info["status"],
                "targets": info["targets"],
                "started_at": info["started_at"]
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
        
        # Limpiar
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
    
    Eventos importantes:
    - CallConnected: La llamada se conecto
    - CallDisconnected: La llamada termino
    - ParticipantsUpdated: Cambios en participantes
    - MediaStreamingStarted: El streaming de audio inicio
    - MediaStreamingStopped: El streaming de audio termino
    """
    try:
        events = await request.json()
        
        # ACS puede enviar multiples eventos
        if not isinstance(events, list):
            events = [events]
        
        for event in events:
            event_type = event.get("type", "")
            call_id = event.get("data", {}).get("callConnectionId", "")
            
            print(f"[ACS Event] {event_type} - Call: {call_id}")
            
            # Log detallado para eventos de error
            if event_type == "Microsoft.Communication.CreateCallFailed":
                data = event.get("data", {})
                result_info = data.get("resultInformation", {})
                error_code = result_info.get("code", "N/A")
                sub_code = result_info.get("subCode", "N/A")
                message = result_info.get("message", "Sin mensaje")
                print(f"[ACS ERROR] CreateCallFailed:")
                print(f"  - Code: {error_code}")
                print(f"  - SubCode: {sub_code}")
                print(f"  - Message: {message}")
                print(f"  - Full data: {json.dumps(data, indent=2)}")
            
            if event_type == "Microsoft.Communication.CallConnected":
                # Llamada conectada - iniciar conexion con OpenAI
                if call_id in active_calls:
                    active_calls[call_id]["status"] = "connected"
                    # Aqui iniciarias la conexion WebSocket con OpenAI
                    asyncio.create_task(connect_to_openai_realtime(call_id))
                    
            elif event_type == "Microsoft.Communication.CallDisconnected":
                # Llamada terminada - obtener razón
                data = event.get("data", {})
                result_info = data.get("resultInformation", {})
                if result_info:
                    print(f"[ACS] CallDisconnected reason: Code={result_info.get('code')}, SubCode={result_info.get('subCode')}, Message={result_info.get('message')}")
                
                if call_id in active_calls:
                    # Cerrar conexion con OpenAI si existe
                    openai_ws = active_calls[call_id].get("openai_ws")
                    if openai_ws:
                        await openai_ws.close()
                    del active_calls[call_id]
                    
            elif event_type == "Microsoft.Communication.MediaStreamingStarted":
                print(f"[ACS] Media streaming iniciado para {call_id}")

            elif event_type == "Microsoft.Communication.MediaStreamingStopped":
                print(f"[ACS] Media streaming detenido para {call_id}")

            elif event_type == "Microsoft.Communication.MediaStreamingFailed":
                # Media streaming falló - obtener detalles
                data = event.get("data", {})
                result_info = data.get("resultInformation", {})
                error_code = result_info.get("code", "N/A")
                sub_code = result_info.get("subCode", "N/A")
                message = result_info.get("message", "Sin mensaje")
                print(f"[ACS ERROR] MediaStreamingFailed:")
                print(f"  - Code: {error_code}")
                print(f"  - SubCode: {sub_code}")
                print(f"  - Message: {message}")
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

    ACS envia audio en formato PCM 16-bit, 16kHz, mono.
    OpenAI Realtime espera PCM 16-bit, 24kHz, mono.

    NOTA: Puede requerir resampling de 16kHz a 24kHz.
    """
    print(f"[Media WS] Intentando aceptar conexion...")
    print(f"[Media WS] Headers: {websocket.headers}")
    print(f"[Media WS] Client: {websocket.client}")

    await websocket.accept()
    print("[Media WS] Conexion aceptada de ACS")

    # Obtener call_id desde los headers (ACS lo envía aquí)
    call_id = websocket.headers.get("x-ms-call-connection-id")
    print(f"[Media WS] Call ID desde headers: {call_id}")

    # Guardar WebSocket inmediatamente si tenemos el call_id
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

            # Primer mensaje contiene metadata
            if "kind" in data:
                if data["kind"] == "AudioMetadata":
                    print(f"[Media WS] AudioMetadata recibido")

                    # Intentar guardar el WebSocket si aún no está guardado
                    if call_id and call_id in active_calls and not active_calls[call_id].get("media_ws"):
                        active_calls[call_id]["media_ws"] = websocket
                        print(f"[Media WS] ✅ WebSocket guardado para {call_id} (desde AudioMetadata)")

                elif data["kind"] == "AudioData":
                    # Audio del usuario
                    audio_data = data.get("audioData", {}).get("data", "")

                    if call_id and call_id in active_calls and audio_data:
                        bot_muted = active_calls[call_id].get("bot_muted", False)

                        if bot_muted:
                            # MODO VIGÍA: Enviar a Whisper para detectar "OPTI"
                            # Esto ahorra dinero porque Whisper es más barato que Realtime
                            await add_audio_to_whisper_buffer(call_id, audio_data)
                        else:
                            # MODO ACTIVO: Enviar a OpenAI Realtime
                            openai_ws = active_calls[call_id].get("openai_ws")

                            if openai_ws:
                                # Resamplear de 16kHz (ACS) a 24kHz (OpenAI)
                                audio_24khz = resample_audio(audio_data, input_rate=16000, output_rate=24000)

                                # Enviar audio a OpenAI Realtime
                                await openai_ws.send(json.dumps({
                                    "type": "input_audio_buffer.append",
                                    "audio": audio_24khz
                                }))
                            else:
                                # OpenAI aun no esta conectado, esperar
                                await asyncio.sleep(0.1)

    except Exception as e:
        print(f"[Media WS] Error: {e}")
    finally:
        # Limpiar referencia al WebSocket de media
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

    Args:
        call_id: ID de la llamada
        retry_count: Número de reintentos realizados
    """
    MAX_RETRIES = 3  # Definir al inicio para uso en except blocks

    if call_id not in active_calls:
        print(f"[OpenAI] Call {call_id} ya no existe en active_calls")
        return

    if retry_count >= MAX_RETRIES:
        print(f"[OpenAI] ❌ Máximo de reintentos alcanzado ({MAX_RETRIES}) para {call_id}")
        return

    if retry_count > 0:
        print(f"[OpenAI] 🔄 Reintento {retry_count}/{MAX_RETRIES} para {call_id}")

    url = "wss://api.openai.com/v1/realtime?model=gpt-realtime-mini-2025-12-15"

    try:
        async with websockets.connect(
            url,
            additional_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            },
            ping_interval=20,  # Enviar ping cada 20 segundos
            ping_timeout=10,   # Timeout de 10 segundos para pong
            close_timeout=10   # Timeout para cierre graceful
        ) as ws:
            # Guardar referencia
            active_calls[call_id]["openai_ws"] = ws
            print(f"[OpenAI] Conectado para llamada: {call_id}")
            
            # Configurar sesion con tools de DB2
            # NOTA: Usamos modalities=["text"] para obtener solo texto (TTS lo hace ACS)
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
                    "tools": tools,  # Agregar herramientas de DB2
                    "temperature": 0.8
                }
            }))
            
            # Saludo inicial - solo en la primera conexión (no en reconexiones)
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
            
            # Procesar mensajes de OpenAI
            async for message in ws:
                if call_id not in active_calls:
                    break

                event = json.loads(message)
                event_type = event.get("type")

                # Audio de respuesta - enviar a ACS
                if event_type == "response.audio.delta":
                    audio_b64 = event.get("delta", "")
                    if audio_b64:
                        # Enviar audio a ACS (con resampling 24kHz → 16kHz)
                        await send_audio_to_acs(call_id, audio_b64)

                elif event_type == "response.audio_transcript.done":
                    # Log del texto para debugging
                    transcript = event.get("transcript", "")
                    if transcript:
                        print(f"[OpenAI] 📝 Dijo: {transcript}")

                elif event_type == "response.done":
                    print(f"[OpenAI] Respuesta completada para {call_id}")

                # Log de otros eventos importantes para debugging
                elif event_type == "response.output_item.added":
                    item = event.get("item", {})
                    if item.get("type") == "function_call":
                        print(f"[OpenAI] 🔧 Function call agregado: {item.get('name')}")

                elif event_type == "response.output_item.done":
                    item = event.get("item", {})
                    if item.get("type") == "function_call":
                        print(f"[OpenAI] 🔧 Function call completado: {item.get('name')}")

                # Manejo de Function Calling
                elif event_type == "response.function_call_arguments.done":
                    # El modelo quiere ejecutar una función
                    function_name = event.get("name")
                    function_args_str = event.get("arguments", "{}")
                    function_call_id = event.get("call_id")  # Este es el ID correcto

                    print(f"[OpenAI] Function call: {function_name}")
                    print(f"[OpenAI] Call ID: {function_call_id}")
                    print(f"[OpenAI] Arguments: {function_args_str}")

                    try:
                        # Parsear argumentos
                        function_args = json.loads(function_args_str) if function_args_str else {}

                        # Manejar función especial set_bot_muted
                        if function_name == "set_bot_muted":
                            muted = function_args.get("muted", False)
                            active_calls[call_id]["bot_muted"] = muted

                            status = "SILENCIADO" if muted else "REACTIVADO"
                            print(f"[BOT] {'🔇' if muted else '🔊'} Comando detectado: Bot {status}")
                            print(f"[BOT] Call ID: {call_id}")

                            if muted:
                                function_result = json.dumps({
                                    "success": True,
                                    "muted": True,
                                    "message": "MODO SILENCIADO ACTIVADO por comando 'OPTI HAZ SILENCIO'. A partir de ahora, SOLO responde a comandos de reactivación que empiecen con 'OPTI' como 'OPTI VUELVE A HABLAR' o 'OPTI HABLA'. IGNORA todas las demás conversaciones, preguntas y menciones de 'silencio' o 'habla' que NO incluyan tu nombre 'OPTI'."
                                })
                            else:
                                function_result = json.dumps({
                                    "success": True,
                                    "muted": False,
                                    "message": "MODO SILENCIADO DESACTIVADO por comando 'OPTI VUELVE A HABLAR'. Ya puedes participar normalmente en la conversación y responder a todas las preguntas. Recuerda que solo debes silenciarte cuando escuches comandos que empiecen con 'OPTI'."
                                })
                        else:
                            # Ejecutar funciones normales (DB2, etc.)
                            function_result = execute_function(function_name, function_args)

                        print(f"[OpenAI] Resultado de función: {function_result[:200]}...")

                        # Enviar resultado de la función a OpenAI
                        await ws.send(json.dumps({
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": function_call_id,  # Usar el ID correcto
                                "output": function_result
                            }
                        }))

                        print(f"[OpenAI] ✅ Resultado enviado para call_id: {function_call_id}")

                        # Solicitar que genere una respuesta con el resultado
                        await ws.send(json.dumps({"type": "response.create"}))

                    except Exception as e:
                        print(f"[OpenAI] Error ejecutando función: {str(e)}")
                        # Enviar error a OpenAI
                        await ws.send(json.dumps({
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": function_call_id,  # Usar el ID correcto
                                "output": json.dumps({"error": str(e)})
                            }
                        }))
                        await ws.send(json.dumps({"type": "response.create"}))

                # Manejo de interrupciones - usuario empieza a hablar
                elif event_type == "input_audio_buffer.speech_started":
                    print(f"[OpenAI] 🎤 Usuario empezó a hablar - INTERRUPCIÓN")
                    # Marcar que el usuario está hablando
                    active_calls[call_id]["user_speaking"] = True
                    # Cancelar la respuesta actual del bot
                    await ws.send(json.dumps({"type": "response.cancel"}))
                    # Detener el audio que se está reproduciendo en ACS
                    await stop_audio_in_acs(call_id)

                elif event_type == "input_audio_buffer.speech_stopped":
                    print(f"[OpenAI] 🎤 Usuario dejó de hablar")
                    # El usuario terminó de hablar, permitir que el bot responda
                    active_calls[call_id]["user_speaking"] = False

                elif event_type == "error":
                    error_data = event.get('error', {})
                    print(f"[OpenAI] ❌ Error event: {error_data}")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"[OpenAI] ⚠️ WebSocket cerrado inesperadamente para {call_id}")
        print(f"[OpenAI] Código: {e.code}, Razón: {e.reason}")

        # Intentar reconectar si la llamada sigue activa
        if call_id in active_calls and active_calls[call_id].get("status") == "connected":
            print(f"[OpenAI] 🔄 Intentando reconectar... (intento {retry_count + 1}/{MAX_RETRIES})")
            await asyncio.sleep(2)  # Esperar 2 segundos antes de reconectar
            await connect_to_openai_realtime(call_id, retry_count + 1)
        else:
            print(f"[OpenAI] Llamada {call_id} ya terminó, no reconectar")

    except websockets.exceptions.WebSocketException as e:
        print(f"[OpenAI] ❌ Error de WebSocket: {type(e).__name__}: {e}")

        # Intentar reconectar
        if call_id in active_calls and retry_count < MAX_RETRIES:
            print(f"[OpenAI] 🔄 Intentando reconectar... (intento {retry_count + 1}/{MAX_RETRIES})")
            await asyncio.sleep(2)
            await connect_to_openai_realtime(call_id, retry_count + 1)

    except asyncio.TimeoutError:
        print(f"[OpenAI] ⏱️ Timeout en la conexión para {call_id}")

        # Intentar reconectar
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

    Args:
        audio_b64: Audio en base64 (PCM 16-bit)
        input_rate: Tasa de muestreo de entrada (Hz)
        output_rate: Tasa de muestreo de salida (Hz)

    Returns:
        Audio resampleado en base64 (PCM 16-bit)
    """
    try:
        # Decodificar de base64
        audio_bytes = base64.b64decode(audio_b64)

        # Convertir bytes a array numpy (int16)
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)

        # Convertir a float para procesamiento
        audio_float = audio_int16.astype(np.float32)

        # Calcular número de muestras de salida
        num_samples = int(len(audio_float) * output_rate / input_rate)

        # Resamplear usando scipy
        resampled = signal.resample(audio_float, num_samples)

        # Convertir de vuelta a int16
        resampled_int16 = np.clip(resampled, -32768, 32767).astype(np.int16)

        # Convertir a bytes y luego a base64
        resampled_bytes = resampled_int16.tobytes()
        resampled_b64 = base64.b64encode(resampled_bytes).decode('utf-8')

        return resampled_b64

    except Exception as e:
        print(f"[Audio] Error resampleando: {e}")
        return audio_b64  # Devolver original si falla


async def stop_audio_in_acs(call_id: str):
    """
    Envía comando para detener el audio actual en ACS.
    Esto permite interrumpir al bot cuando el usuario empieza a hablar.

    Args:
        call_id: ID de la llamada
    """
    if call_id not in active_calls:
        return

    media_ws = active_calls[call_id].get("media_ws")
    if not media_ws:
        return

    try:
        # Comando para detener audio según documentación de ACS
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
    Convierte de 24kHz (OpenAI) a 16kHz (ACS).

    Args:
        call_id: ID de la llamada
        audio_b64: Audio en base64 desde OpenAI (PCM 16-bit, 24kHz)
    """
    if call_id not in active_calls:
        return

    # Verificar si el bot está silenciado o si hay interrupción activa
    if active_calls[call_id].get("bot_muted", False):
        return  # No enviar audio si está silenciado

    if active_calls[call_id].get("user_speaking", False):
        return  # No enviar audio si el usuario está hablando (interrupción)

    media_ws = active_calls[call_id].get("media_ws")

    if not media_ws:
        return

    try:
        # Resamplear de 24kHz a 16kHz
        audio_16khz = resample_audio(audio_b64, input_rate=24000, output_rate=16000)

        # Formato de mensaje para ACS - DEBE usar mayúsculas según documentación
        message = {
            "Kind": "AudioData",  # Mayúscula
            "AudioData": {
                "Data": audio_16khz  # Mayúscula
            },
            "StopAudio": None
        }

        # Enviar a ACS
        await media_ws.send_text(json.dumps(message))

    except Exception as e:
        print(f"[Audio] Error enviando a ACS: {e}")


# ============================================================================
# WHISPER API (Modo vigía - detección de palabra clave)
# ============================================================================

# Configuración de Whisper
WHISPER_BUFFER_DURATION_SECONDS = 5  # Cada cuántos segundos enviar a Whisper
WHISPER_SAMPLE_RATE = 16000  # 16kHz (formato de ACS)
WHISPER_BYTES_PER_SECOND = WHISPER_SAMPLE_RATE * 2  # 16-bit = 2 bytes por muestra
WHISPER_BUFFER_SIZE = WHISPER_BUFFER_DURATION_SECONDS * WHISPER_BYTES_PER_SECOND


def pcm_to_wav(pcm_data: bytes, sample_rate: int = 16000) -> bytes:
    """
    Convierte audio PCM raw a formato WAV para Whisper API.

    Args:
        pcm_data: Audio en bytes (PCM 16-bit mono)
        sample_rate: Tasa de muestreo (default 16kHz)

    Returns:
        Audio en formato WAV como bytes
    """
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit = 2 bytes
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    wav_buffer.seek(0)
    return wav_buffer.read()


async def transcribe_with_whisper(audio_bytes: bytes) -> str:
    """
    Envía audio a OpenAI Whisper API para transcripción.

    Args:
        audio_bytes: Audio en formato PCM 16-bit, 16kHz, mono

    Returns:
        Texto transcrito o string vacío si falla
    """
    try:
        # Convertir PCM a WAV
        wav_data = pcm_to_wav(audio_bytes)

        # Preparar request para Whisper API
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
                    "language": "es"  # Español
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
    Procesa el buffer de audio acumulado con Whisper y detecta la palabra clave "OPTI".
    Si detecta "OPTI", reactiva el bot y envía el audio a OpenAI Realtime.

    Args:
        call_id: ID de la llamada
    """
    if call_id not in active_calls:
        return

    call_data = active_calls[call_id]
    audio_buffer = call_data.get("whisper_buffer", b"")

    # Verificar si hay suficiente audio
    if len(audio_buffer) < WHISPER_BUFFER_SIZE:
        return

    # Extraer el buffer para procesar
    buffer_to_process = audio_buffer[:WHISPER_BUFFER_SIZE]
    call_data["whisper_buffer"] = audio_buffer[WHISPER_BUFFER_SIZE:]

    # Transcribir con Whisper
    transcript = await transcribe_with_whisper(buffer_to_process)

    if not transcript:
        return

    # Buscar palabra clave "OPTI" (case insensitive)
    transcript_upper = transcript.upper()

    if "OPTI" in transcript_upper:
        print(f"[Whisper] 🎯 Palabra clave 'OPTI' detectada!")
        print(f"[Whisper] 📣 Reactivando bot para call {call_id}")

        # Desmutar el bot
        call_data["bot_muted"] = False

        # Limpiar el buffer de Whisper
        call_data["whisper_buffer"] = b""

        # Enviar el contexto a OpenAI Realtime para que responda
        openai_ws = call_data.get("openai_ws")
        if openai_ws:
            try:
                # Enviar mensaje de texto con lo que dijo el usuario
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

    Args:
        call_id: ID de la llamada
        audio_b64: Audio en base64 (PCM 16-bit, 16kHz de ACS)
    """
    if call_id not in active_calls:
        return

    try:
        # Decodificar audio
        audio_bytes = base64.b64decode(audio_b64)

        # Agregar al buffer
        call_data = active_calls[call_id]
        if "whisper_buffer" not in call_data:
            call_data["whisper_buffer"] = b""

        call_data["whisper_buffer"] += audio_bytes

        # Procesar si hay suficiente audio
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
    
    # Lunes a Viernes
    if now.weekday() >= 5:  # Sabado (5) o Domingo (6)
        return False
    
    # 8:00 AM a 6:00 PM
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
