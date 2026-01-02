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

# Azure Communication Services
from azure.communication.callautomation import CallAutomationClient
from azure.communication.callautomation import PhoneNumberIdentifier

load_dotenv()

# Configuracion
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")
CALLBACK_URI = os.getenv("CALLBACK_URI")  # URL publica - usar ngrok para desarrollo

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
            from azure.communication.callautomation import MicrosoftTeamsUserIdentifier
            target = MicrosoftTeamsUserIdentifier(request.target_number)
        else:
            # Llamada telefonica PSTN
            target = PhoneNumberIdentifier(request.target_number)
        
        # Crear la llamada
        # NOTA: Para PSTN necesitas especificar source_caller_id_number (tu numero ACS)
        call_result = acs_client.create_call(
            target_participant=target,
            callback_url=f"{CALLBACK_URI}/callbacks/acs"
        )
        
        call_id = call_result.call_connection_id
        
        # Guardar info de la llamada
        active_calls[call_id] = {
            "call_id": call_id,
            "status": "connecting",
            "target": request.target_number,
            "target_type": request.target_type,
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
            
            if event_type == "Microsoft.Communication.CallConnected":
                # Llamada conectada - iniciar conexion con OpenAI
                if call_id in active_calls:
                    active_calls[call_id]["status"] = "connected"
                    # Aqui iniciarias la conexion WebSocket con OpenAI
                    asyncio.create_task(connect_to_openai_realtime(call_id))
                    
            elif event_type == "Microsoft.Communication.CallDisconnected":
                # Llamada terminada
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
    await websocket.accept()
    
    call_id = None
    openai_ws = None
    
    try:
        async for message in websocket.iter_text():
            data = json.loads(message)
            
            # Primer mensaje contiene metadata
            if "kind" in data:
                if data["kind"] == "AudioMetadata":
                    call_id = data.get("audioMetadata", {}).get("callConnectionId")
                    print(f"[Media WS] Conectado para llamada: {call_id}")
                    
                    # Obtener conexion OpenAI de la llamada
                    if call_id and call_id in active_calls:
                        openai_ws = active_calls[call_id].get("openai_ws")
                        
                elif data["kind"] == "AudioData":
                    # Audio del usuario - enviar a OpenAI
                    audio_data = data.get("audioData", {}).get("data", "")
                    
                    if openai_ws and audio_data:
                        # Enviar audio a OpenAI Realtime
                        # NOTA: Aqui podrias necesitar resampling 16kHz -> 24kHz
                        await openai_ws.send(json.dumps({
                            "type": "input_audio_buffer.append",
                            "audio": audio_data  # Ya viene en base64
                        }))
                        
    except Exception as e:
        print(f"[Media WS] Error: {e}")
    finally:
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
            
            # Configurar sesion
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
                    }
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
                        # TODO: Enviar audio a ACS via el WebSocket de media
                        # Esto requiere tener referencia al websocket de ACS
                        pass
                
                elif event_type == "response.done":
                    print(f"[OpenAI] Respuesta completada para {call_id}")
                    
                elif event_type == "error":
                    print(f"[OpenAI] Error: {event.get('error')}")
                    
    except Exception as e:
        print(f"[OpenAI] Error de conexion: {e}")
    finally:
        if call_id in active_calls:
            active_calls[call_id]["openai_ws"] = None
        print(f"[OpenAI] Desconectado para llamada: {call_id}")


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
