from fastapi import FastAPI, Request, WebSocket, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import json
import asyncio
import websockets
import base64
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import numpy as np
from scipy import signal

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
    """Solicitud para hacer una llamada saliente"""
    target_number: str  # Numero de telefono o ID de Teams
    target_type: str = "phone"  # "phone" o "teams"
    display_name: str = "Optinoc VoiceBot"  # Nombre que aparece en Teams (opcional)
    

class CallInfo(BaseModel):
    """Informacion de una llamada"""
    call_id: str
    status: str
    target: str
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
    Inicia una llamada saliente a un numero de telefono o usuario de Teams.
    
    - Para telefono: target_number = "+573001234567"
    - Para Teams: target_number = "user@empresa.com" (requiere Teams interop)
    
    NOTA: Requiere configurar ACS con un numero de telefono comprado.
    """
    if not acs_client:
        raise HTTPException(status_code=503, detail="ACS no configurado. Configura ACS_CONNECTION_STRING en .env")
    
    if not CALLBACK_URI:
        raise HTTPException(
            status_code=503, 
            detail="CALLBACK_URI no configurado. Usa ngrok y configura la URL en .env"
        )
    
    try:
        # Determinar el tipo de destino
        if request.target_type == "teams":
            # Llamada a Teams (requiere Teams interoperability habilitado en ACS)
            from azure.communication.callautomation import MicrosoftTeamsUserIdentifier, CommunicationCloudEnvironment

            # Determinar el formato del identificador
            if "@" in request.target_number and "." in request.target_number:
                # Es un email/UPN (user@domain.com) - NO soportado directamente, necesita Object ID
                raise HTTPException(
                    status_code=400,
                    detail="Para llamadas a Teams usa el Object ID del usuario (GUID), no el email/UPN"
                )
            else:
                # Es un Object ID
                if not TENANT_ID:
                    raise HTTPException(
                        status_code=503,
                        detail="TENANT_ID no configurado en .env. Necesario para llamadas a Teams"
                    )
                user_id = request.target_number
                print(f"[CALL] Usando Object ID para Teams: {user_id}")
                print(f"[CALL] Tenant ID: {TENANT_ID}")

            # Crear identificador de Teams con cloud environment
            target = MicrosoftTeamsUserIdentifier(
                user_id=user_id,
                cloud=CommunicationCloudEnvironment.PUBLIC
            )
        else:
            # Llamada telefonica PSTN
            target = PhoneNumberIdentifier(request.target_number)
        
        # Configurar media streaming para audio bidireccional
        # Convertir https:// a wss:// para WebSocket
        websocket_url = CALLBACK_URI.replace("https://", "wss://").replace("http://", "ws://")
        media_streaming = MediaStreamingOptions(
            transport_url=f"{websocket_url}/ws/media",
            transport_type=StreamingTransportType.WEBSOCKET,
            content_type=MediaStreamingContentType.AUDIO,
            audio_channel_type=MediaStreamingAudioChannelType.MIXED,
            start_media_streaming=True,
            enable_bidirectional=True,  # CRÍTICO: Habilita envío de audio de vuelta
            audio_format=AudioFormat.PCM16_K_MONO  # 16kHz PCM mono
        )
        print(f"[CALL] WebSocket URL: {websocket_url}/ws/media")
        print(f"[CALL] Bidirectional audio: ENABLED")

        # Crear la llamada
        # NOTA: Para PSTN necesitas especificar source_caller_id_number (tu numero ACS)
        call_result = acs_client.create_call(
            target_participant=target,
            callback_url=f"{CALLBACK_URI}/callbacks/acs",
            media_streaming=media_streaming,
            source_display_name=request.display_name  # Nombre que aparece en Teams
        )
        
        call_id = call_result.call_connection_id
        
        # Guardar info de la llamada
        active_calls[call_id] = {
            "call_id": call_id,
            "status": "connecting",
            "target": request.target_number,
            "target_type": request.target_type,
            "target_participant": target,  # Guardar el identificador del participante
            "started_at": datetime.now().isoformat(),
            "openai_ws": None
        }
        
        print(f"[CALL] Llamada iniciada: {call_id} -> {request.target_number}")
        
        return CallInfo(
            call_id=call_id,
            status="connecting",
            target=request.target_number,
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
                "target": info["target"],
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
                    # Audio del usuario - enviar a OpenAI (sin logging para no saturar)
                    audio_data = data.get("audioData", {}).get("data", "")

                    if call_id and call_id in active_calls:
                        openai_ws = active_calls[call_id].get("openai_ws")

                        if openai_ws and audio_data:
                            # Resamplear de 16kHz (ACS) a 24kHz (OpenAI)
                            audio_24khz = resample_audio(audio_data, input_rate=16000, output_rate=24000)

                            # Enviar audio a OpenAI Realtime
                            await openai_ws.send(json.dumps({
                                "type": "input_audio_buffer.append",
                                "audio": audio_24khz
                            }))
                        elif not openai_ws:
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

async def connect_to_openai_realtime(call_id: str):
    """
    Establece conexion WebSocket con OpenAI Realtime API
    y maneja el flujo de audio bidireccional.
    """
    if call_id not in active_calls:
        return
    
    url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
    
    try:
        async with websockets.connect(
            url,
            additional_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            }
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
            
            # Saludo inicial
            await asyncio.sleep(0.5)
            await ws.send(json.dumps({
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user", 
                    "content": [{"type": "input_text", "text": "Saluda al usuario"}]
                }
            }))
            await ws.send(json.dumps({"type": "response.create"}))
            
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

                # Manejo de Function Calling
                elif event_type == "response.function_call_arguments.done":
                    # El modelo quiere ejecutar una función
                    function_name = event.get("name")
                    function_args_str = event.get("arguments", "{}")
                    call_item_id = event.get("item_id")

                    print(f"[OpenAI] Function call: {function_name} con args: {function_args_str}")

                    try:
                        # Parsear argumentos (aunque por ahora nuestras funciones no los usan)
                        function_args = json.loads(function_args_str) if function_args_str else {}

                        # Ejecutar la función
                        function_result = execute_function(function_name, function_args)

                        print(f"[OpenAI] Resultado de función: {function_result[:200]}...")

                        # Enviar resultado de la función a OpenAI
                        await ws.send(json.dumps({
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": call_item_id,
                                "output": function_result
                            }
                        }))

                        # Solicitar que genere una respuesta con el resultado
                        await ws.send(json.dumps({"type": "response.create"}))

                    except Exception as e:
                        print(f"[OpenAI] Error ejecutando función: {str(e)}")
                        # Enviar error a OpenAI
                        await ws.send(json.dumps({
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": call_item_id,
                                "output": json.dumps({"error": str(e)})
                            }
                        }))
                        await ws.send(json.dumps({"type": "response.create"}))

                elif event_type == "error":
                    print(f"[OpenAI] Error: {event.get('error')}")
                    
    except Exception as e:
        print(f"[OpenAI] Error de conexion: {e}")
    finally:
        if call_id in active_calls:
            active_calls[call_id]["openai_ws"] = None
        print(f"[OpenAI] Desconectado para llamada: {call_id}")


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


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
