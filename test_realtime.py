import asyncio
import websockets
import json
import base64
import pyaudio
import os
from dotenv import load_dotenv
from functions import tools, available_functions, execute_function

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configuracion de audio - PCM16, mono, 24kHz (requerido por OpenAI Realtime)
CHUNK = 4800  # 200ms de audio a 24kHz
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000

with open('prompt.txt', 'r') as file:
    prompt = file.read()


async def test_realtime():
    """Prueba simple de GPT-4o Realtime con microfono"""
    
    # Modelo actualizado
    url = "wss://api.openai.com/v1/realtime?model=gpt-realtime-2025-08-28"
    
    # Iniciar PyAudio
    audio = pyaudio.PyAudio()
    
    # Stream de entrada (micrófono)
    stream_in = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    # Stream de salida (bocinas)
    stream_out = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        output=True,
        frames_per_buffer=CHUNK
    )
    
    print("🎙️ Conectando a OpenAI Realtime...")
    
    try:
        async with websockets.connect(
            url,
            additional_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            }
        ) as ws:
            
            print("✅ Conectado!")
            
            # Esperar evento session.created antes de configurar
            print("Esperando session.created...")
            
            # Configurar sesion
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": prompt,
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.8,              # Mas alto = menos sensible al ruido (0.0-1.0)
                        "prefix_padding_ms": 500,      # Mas padding antes de detectar voz
                        "silence_duration_ms": 1000    # Esperar mas silencio antes de responder
                    },
                    "tools": tools,
                    "tool_choice": "auto"
                }
            }
            
            await ws.send(json.dumps(session_config))
            print("Configuracion de sesion enviada...")
            
            # Esperar confirmacion
            await asyncio.sleep(1)
            
            # Crear mensaje inicial de texto para que el asistente responda
            await ws.send(json.dumps({
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Hola"
                        }
                    ]
                }
            }))
            
            # Solicitar respuesta
            await ws.send(json.dumps({
                "type": "response.create"
            }))
            
            print("🔊 Escucha por tus bocinas...")
            print("🗣️ Luego puedes hablar por el micrófono")
            print("⌨️  Presiona Ctrl+C cuando quieras terminar\n")
            
            async def send_audio():
                """Enviar audio del micrófono a OpenAI"""
                await asyncio.sleep(3)  # Esperar 3 segundos antes de empezar a enviar
                try:
                    while True:
                        data = stream_in.read(CHUNK, exception_on_overflow=False)
                        audio_b64 = base64.b64encode(data).decode('utf-8')
                        
                        await ws.send(json.dumps({
                            "type": "input_audio_buffer.append",
                            "audio": audio_b64
                        }))
                        
                        await asyncio.sleep(0.01)
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    print(f"❌ Error enviando audio: {e}")
            
            # Variables para controlar el estado
            response_active = False  # Hay una respuesta en curso
            pending_function_call = {}  # Para acumular argumentos de function call

            async def receive_audio():
                """Recibir audio de OpenAI y reproducirlo"""
                nonlocal response_active, pending_function_call
                audio_chunks_received = 0
                try:
                    async for message in ws:
                        event = json.loads(message)
                        event_type = event.get("type")
                        
                        # Usuario empezo a hablar - INTERRUPCION
                        if event_type == "input_audio_buffer.speech_started":
                            if response_active:
                                print("\n[INTERRUPCION] Usuario hablando, cancelando respuesta...")
                                await ws.send(json.dumps({"type": "response.cancel"}))
                        
                        # Respuesta iniciada
                        elif event_type == "response.created":
                            response_active = True
                        
                        # Audio de respuesta
                        elif event_type == "response.audio.delta":
                            audio_b64 = event.get("delta", "")
                            if audio_b64:
                                audio_data = base64.b64decode(audio_b64)
                                stream_out.write(audio_data)
                                audio_chunks_received += 1
                                if audio_chunks_received == 1:
                                    print(f"[AUDIO] Recibiendo audio...")
                        
                        # Audio del asistente termino
                        elif event_type == "response.audio.done":
                            if audio_chunks_received > 0:
                                print(f"[AUDIO] Audio completado. Total chunks: {audio_chunks_received}")
                            audio_chunks_received = 0
                        
                        # Respuesta terminada (completada o cancelada)
                        elif event_type == "response.done":
                            response_active = False
                            status = event.get("response", {}).get("status", "completed")
                            if status == "cancelled":
                                print("--- Respuesta cancelada ---\n")
                            else:
                                print("--- Respuesta completada ---\n")
                        
                        # Transcripcion de lo que dijiste
                        elif event_type == "conversation.item.input_audio_transcription.completed":
                            transcript = event.get("transcript", "")
                            if transcript:
                                print(f"Tu: {transcript}")
                        
                        # Transcripcion de lo que dijo el asistente
                        elif event_type == "response.audio_transcript.delta":
                            transcript = event.get("delta", "")
                            if transcript:
                                print(transcript, end="", flush=True)
                        
                        elif event_type == "response.audio_transcript.done":
                            print()  # Nueva linea al terminar

                        # Function call - el modelo quiere usar una herramienta
                        elif event_type == "response.output_item.added":
                            item = event.get("item", {})
                            if item.get("type") == "function_call":
                                pending_function_call = {
                                    "call_id": item.get("call_id"),
                                    "name": item.get("name"),
                                    "arguments": ""
                                }
                                print(f"\n[FUNCTION] Modelo llamando: {item.get('name')}")

                        # Argumentos de function call (streaming)
                        elif event_type == "response.function_call_arguments.delta":
                            delta = event.get("delta", "")
                            if pending_function_call:
                                pending_function_call["arguments"] += delta

                        # Function call completo - ejecutar la funcion
                        elif event_type == "response.function_call_arguments.done":
                            if pending_function_call:
                                func_name = pending_function_call.get("name")
                                call_id = pending_function_call.get("call_id")
                                args_str = pending_function_call.get("arguments", "{}")

                                print(f"[FUNCTION] Argumentos: {args_str}")

                                # Parsear argumentos y ejecutar funcion
                                try:
                                    args = json.loads(args_str) if args_str else {}

                                    # Usar execute_function que maneja todo correctamente
                                    result = execute_function(func_name, args)
                                    print(f"[FUNCTION] Resultado: {result[:200]}...")

                                    # Enviar resultado de vuelta a OpenAI
                                    await ws.send(json.dumps({
                                        "type": "conversation.item.create",
                                        "item": {
                                            "type": "function_call_output",
                                            "call_id": call_id,
                                            "output": result
                                        }
                                    }))

                                    # Solicitar que el modelo continue respondiendo
                                    await ws.send(json.dumps({
                                        "type": "response.create"
                                    }))

                                except json.JSONDecodeError as e:
                                    print(f"[FUNCTION] Error parseando argumentos: {e}")
                                except Exception as e:
                                    print(f"[FUNCTION] Error ejecutando: {e}")

                                pending_function_call = {}

                        # Ignorar errores de cancel cuando no hay respuesta activa
                        elif event_type == "error":
                            error_code = event.get("error", {}).get("code", "")
                            if error_code != "response_cancel_not_active":
                                print(f"ERROR: {event.get('error')}")
                            
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    print(f"❌ Error recibiendo audio: {e}")
            
            # Ejecutar ambos en paralelo
            try:
                await asyncio.gather(send_audio(), receive_audio())
            except KeyboardInterrupt:
                print("\n\n👋 Terminando conversación...")
            
    finally:
        print("🔌 Cerrando conexiones...")
        stream_in.stop_stream()
        stream_in.close()
        stream_out.stop_stream()
        stream_out.close()
        audio.terminate()
        print("✅ Prueba finalizada")


if __name__ == "__main__":
    try:
        asyncio.run(test_realtime())
    except KeyboardInterrupt:
        print("\n👋 Adiós!")