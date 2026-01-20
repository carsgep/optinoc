# Azure Communication Services - Call Automation Skills

## Instalacion

```bash
pip install azure-communication-callautomation
pip install azure-identity
```

**Requisitos:**
- Python 3.8+
- Suscripcion Azure activa
- Recurso Azure Communication Services desplegado

---

## Autenticacion

### Opcion 1: Connection String
```python
from azure.communication.callautomation import CallAutomationClient

connection_string = "<ACS_CONNECTION_STRING>"
client = CallAutomationClient.from_connection_string(connection_string)
```

### Opcion 2: Azure Identity (DefaultAzureCredential)
```python
from azure.identity import DefaultAzureCredential
from azure.communication.callautomation import CallAutomationClient

endpoint = "https://<resource-name>.communication.azure.com"
credential = DefaultAzureCredential()
client = CallAutomationClient(endpoint, credential)
```

---

## Clases Principales

| Clase | Descripcion |
|-------|-------------|
| `CallAutomationClient` | Cliente principal para crear/responder llamadas y grabacion |
| `CallConnectionClient` | Maneja una llamada establecida (transferir, reproducir, colgar) |
| `PhoneNumberIdentifier` | Identifica un numero telefonico PSTN |
| `MicrosoftTeamsUserIdentifier` | Identifica un usuario de Microsoft Teams |
| `CommunicationUserIdentifier` | Identifica un usuario de ACS |

---

## Llamadas Salientes

### Llamada a Numero Telefonico (PSTN)
```python
from azure.communication.callautomation import (
    CallAutomationClient,
    PhoneNumberIdentifier,
    CallInvite
)

# Crear cliente
client = CallAutomationClient.from_connection_string(connection_string)

# Destino y origen
target = PhoneNumberIdentifier("+573001234567")
source = PhoneNumberIdentifier("+1XXXXXXXXXX")  # Numero ACS comprado

# Crear invitacion
call_invite = CallInvite(
    target=target,
    source_caller_id_number=source
)

# Iniciar llamada
result = client.create_call(
    call_invite,
    callback_url="https://tu-servidor.com/callbacks/acs"
)

call_connection_id = result.call_connection_id
```

### Llamada a Usuario de Teams
```python
from azure.communication.callautomation import MicrosoftTeamsUserIdentifier

# Usuario Teams (requiere Teams interop habilitado)
target = MicrosoftTeamsUserIdentifier("usuario@empresa.com")

call_invite = CallInvite(target=target)

result = client.create_call(
    call_invite,
    callback_url="https://tu-servidor.com/callbacks/acs"
)
```

### Llamada con Cognitive Services (TTS/STT)
```python
result = client.create_call(
    call_invite,
    callback_url=callback_url,
    cognitive_services_endpoint="https://<cognitive-services>.cognitiveservices.azure.com"
)
```

---

## Responder Llamadas Entrantes

```python
# El incoming_call_context viene del evento IncomingCall de EventGrid
result = client.answer_call(
    incoming_call_context=incoming_call_context,
    callback_url="https://tu-servidor.com/callbacks/acs"
)
```

---

## Media Streaming Bidireccional

### Configuracion de Streaming
```python
from azure.communication.callautomation import (
    MediaStreamingOptions,
    StreamingTransportType,
    MediaStreamingContentType,
    MediaStreamingAudioChannelType,
    AudioFormat
)

media_streaming_options = MediaStreamingOptions(
    transport_url="wss://tu-servidor.com/ws/media",
    transport_type=StreamingTransportType.WEBSOCKET,
    content_type=MediaStreamingContentType.AUDIO,
    audio_channel_type=MediaStreamingAudioChannelType.MIXED,
    start_media_streaming=True,
    enable_bidirectional=True,       # Permite enviar audio de vuelta
    enable_dtmf_tones=True,          # Detecta tonos DTMF
    audio_format=AudioFormat.PCM24_K_MONO  # O PCM16_K_MONO
)
```

### Responder con Streaming
```python
result = client.answer_call(
    incoming_call_context=incoming_call_context,
    callback_url=callback_url,
    media_streaming=media_streaming_options
)
```

### Iniciar Streaming en Llamada Activa
```python
call_connection = client.get_call_connection(call_connection_id)
call_connection.start_media_streaming(
    operation_context="startMediaStreamingContext"
)
```

### Detener Streaming
```python
call_connection.stop_media_streaming(
    operation_context="stopMediaStreamingContext"
)
```

---

## Formatos de Audio WebSocket

### Recibir Audio (desde ACS)

**Metadata (primer mensaje):**
```json
{
  "kind": "AudioMetadata",
  "audioMetadata": {
    "subscriptionId": "uuid",
    "encoding": "PCM",
    "sampleRate": 16000,
    "channels": 1,
    "length": 640
  }
}
```

**Datos de Audio:**
```json
{
  "kind": "AudioData",
  "audioData": {
    "timestamp": "2024-11-15T19:16:12.925Z",
    "participantRawID": "8:acs:xxxx",
    "data": "<base64_pcm_audio>",
    "silent": false
  }
}
```

**DTMF Tones:**
```json
{
  "kind": "DtmfData",
  "dtmfData": {
    "data": "3"
  }
}
```

### Enviar Audio (hacia ACS)

**Enviar chunk de audio:**
```json
{
  "Kind": "AudioData",
  "AudioData": {
    "Data": "<base64_pcm_audio>"
  },
  "StopAudio": null
}
```

**Detener reproduccion:**
```json
{
  "Kind": "StopAudio",
  "AudioData": null,
  "StopAudio": {}
}
```

---

## Reproducir Audio

### Reproducir Archivo de Audio
```python
from azure.communication.callautomation import FileSource

call_connection = client.get_call_connection(call_connection_id)

audio_file = FileSource(url="https://storage.blob.core.windows.net/audio/saludo.wav")
call_connection.play_media_to_all(audio_file)
```

### Text-to-Speech (requiere Cognitive Services)
```python
from azure.communication.callautomation import TextSource

text_source = TextSource(
    text="Hola, bienvenido al sistema de atencion automatizada.",
    voice_name="es-MX-DaliaNeural"  # Voz en espanol
)

call_connection.play_media_to_all(text_source)
```

### Reproducir a Participante Especifico
```python
call_connection.play_media(
    play_source=text_source,
    play_to=[target_participant]
)
```

---

## Reconocimiento de Voz y DTMF

### Reconocer DTMF
```python
from azure.communication.callautomation import (
    RecognizeInputType,
    DtmfTone
)

call_connection.start_recognizing_media(
    input_type=RecognizeInputType.DTMF,
    target_participant=target,
    initial_silence_timeout=10,
    dtmf_inter_tone_timeout=5,
    dtmf_max_tones_to_collect=1,
    stop_dtmf_tones=[DtmfTone.POUND]
)
```

### Reconocer Voz con Opciones
```python
from azure.communication.callautomation import RecognitionChoice

choices = [
    RecognitionChoice(
        label="Confirmar",
        phrases=["Confirmar", "Si", "Correcto", "Uno"],
        tone=DtmfTone.ONE
    ),
    RecognitionChoice(
        label="Cancelar",
        phrases=["Cancelar", "No", "Dos"],
        tone=DtmfTone.TWO
    )
]

prompt = TextSource(
    text="Presione 1 o diga Confirmar para aceptar. Presione 2 o diga Cancelar para rechazar.",
    voice_name="es-MX-DaliaNeural"
)

call_connection.start_recognizing_media(
    input_type=RecognizeInputType.CHOICES,
    target_participant=target,
    choices=choices,
    play_prompt=prompt,
    interrupt_prompt=False,
    initial_silence_timeout=10,
    operation_context="menu_principal"
)
```

### Reconocer Voz Libre (Speech-to-Text)
```python
call_connection.start_recognizing_media(
    input_type=RecognizeInputType.SPEECH,
    target_participant=target,
    end_silence_timeout=3,
    speech_language="es-MX",
    operation_context="input_libre"
)
```

---

## Grabacion de Llamadas

### Iniciar Grabacion
```python
from azure.communication.callautomation import ServerCallLocator

# server_call_id viene del evento CallConnected
recording_properties = client.start_recording(
    ServerCallLocator(server_call_id)
)

recording_id = recording_properties.recording_id
```

### Pausar/Reanudar Grabacion
```python
client.pause_recording(recording_id)
client.resume_recording(recording_id)
```

### Detener Grabacion
```python
client.stop_recording(recording_id)
```

### Obtener Estado de Grabacion
```python
state = client.get_recording_properties(recording_id)
print(state.recording_state)  # active, inactive
```

---

## Control de Llamada

### Obtener Conexion de Llamada
```python
call_connection = client.get_call_connection(call_connection_id)
```

### Colgar Llamada
```python
# Colgar para todos los participantes
call_connection.hang_up(is_for_everyone=True)

# Solo abandonar la llamada (otros siguen)
call_connection.hang_up(is_for_everyone=False)
```

### Transferir Llamada
```python
# Transferencia ciega
call_connection.transfer_call_to_participant(
    target_participant=PhoneNumberIdentifier("+573009876543")
)
```

### Agregar Participante
```python
call_connection.add_participant(
    target_participant=PhoneNumberIdentifier("+573001111111")
)
```

### Remover Participante
```python
call_connection.remove_participant(
    target_participant=participant_to_remove
)
```

### Cancelar Operaciones de Media
```python
call_connection.cancel_all_media_operations()
```

---

## Eventos de Callback (Webhooks)

### Eventos Principales

| Evento | Descripcion |
|--------|-------------|
| `CallConnected` | Llamada establecida |
| `CallDisconnected` | Llamada terminada |
| `CallTransferAccepted` | Transferencia aceptada |
| `CallTransferFailed` | Transferencia fallida |
| `ParticipantsUpdated` | Cambio en participantes |
| `RecognizeCompleted` | Reconocimiento exitoso |
| `RecognizeFailed` | Reconocimiento fallido |
| `PlayCompleted` | Reproduccion completada |
| `PlayFailed` | Reproduccion fallida |
| `MediaStreamingStarted` | Streaming de media iniciado |
| `MediaStreamingStopped` | Streaming de media detenido |
| `RecordingStateChanged` | Estado de grabacion cambio |

### Procesar Eventos (Flask/FastAPI)
```python
from azure.core.messaging import CloudEvent

@app.post("/callbacks/acs")
async def handle_callback(request: Request):
    events = await request.json()

    for event_dict in events:
        event = CloudEvent.from_dict(event_dict)
        event_type = event.type
        data = event.data

        call_connection_id = data.get("callConnectionId")

        if event_type == "Microsoft.Communication.CallConnected":
            server_call_id = data.get("serverCallId")
            # Llamada conectada - iniciar logica

        elif event_type == "Microsoft.Communication.CallDisconnected":
            # Llamada terminada - limpiar recursos

        elif event_type == "Microsoft.Communication.RecognizeCompleted":
            recognition_type = data.get("recognitionType")

            if recognition_type == "choices":
                label = data["choiceResult"]["label"]
                phrase = data["choiceResult"]["recognizedPhrase"]

            elif recognition_type == "dtmf":
                tones = data["dtmfResult"]["tones"]

            elif recognition_type == "speech":
                speech_text = data["speechResult"]["speech"]

        elif event_type == "Microsoft.Communication.PlayCompleted":
            # Audio termino de reproducirse

        elif event_type == "Microsoft.Communication.MediaStreamingStarted":
            # Streaming de audio listo

    return {"status": "ok"}
```

---

## Voces TTS Disponibles (Espanol)

| Voz | Idioma | Genero |
|-----|--------|--------|
| `es-MX-DaliaNeural` | Espanol Mexico | Femenino |
| `es-MX-JorgeNeural` | Espanol Mexico | Masculino |
| `es-ES-ElviraNeural` | Espanol Espana | Femenino |
| `es-ES-AlvaroNeural` | Espanol Espana | Masculino |
| `es-CO-GonzaloNeural` | Espanol Colombia | Masculino |
| `es-CO-SalomeNeural` | Espanol Colombia | Femenino |
| `es-AR-ElenaNeural` | Espanol Argentina | Femenino |
| `es-AR-TomasNeural` | Espanol Argentina | Masculino |

---

## Variables de Entorno Requeridas

```bash
# Azure Communication Services
ACS_CONNECTION_STRING=endpoint=https://xxx.communication.azure.com/;accesskey=xxx

# Numero telefonico ACS (para llamadas PSTN)
ACS_PHONE_NUMBER=+1XXXXXXXXXX

# URL publica para callbacks (usar ngrok en desarrollo)
CALLBACK_URI=https://tu-dominio.com

# Azure Cognitive Services (opcional, para TTS/STT)
COGNITIVE_SERVICES_ENDPOINT=https://xxx.cognitiveservices.azure.com

# WebSocket para media streaming
WEBSOCKET_URI=wss://tu-dominio.com/ws/media
```

---

## Flujo Tipico de Llamada con IA

```
1. Trigger externo solicita llamada
   ↓
2. create_call() con media_streaming habilitado
   ↓
3. CallConnected event → WebSocket conectado
   ↓
4. ACS envia audio del usuario via WebSocket
   ↓
5. Audio se procesa (OpenAI Realtime, etc.)
   ↓
6. Respuesta de audio se envia via WebSocket a ACS
   ↓
7. Usuario escucha respuesta
   ↓
8. Ciclo se repite hasta hang_up()
```
