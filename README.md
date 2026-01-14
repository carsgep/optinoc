# Optinoc BOCC Realtime

Servidor FastAPI que actua como puente bidireccional entre Azure Communication Services (ACS) y GPT-4o Realtime API de OpenAI para conversaciones de voz en tiempo real.

## Objetivo Principal

Permitir que un asistente de IA de voz (GPT-4o) pueda hacer llamadas automaticas a personas y mantener conversaciones naturales en tiempo real.

## Escenarios de Llamada

| Escenario | Cuando | Canal |
|-----------|--------|-------|
| Horario laboral | Dias y horas habiles | Llamadas a Microsoft Teams (via Teams interoperability de ACS) |
| Fuera de horario | Noches, fines de semana | Llamadas a telefonos tradicionales (via SIP trunking con Cisco) |

## Arquitectura

```
[Trigger Externo] --> [FastAPI Server] --> [Azure Communication Services]
                            |                         |
                            v                         v
                    [GPT-4o Realtime] <--> [WebSocket bidireccional]
                            |                         |
                            v                         v
                    [Audio PCM 24kHz] <--> [Usuario en Teams/Telefono]
```

## Caracteristicas Clave

- **Relay de audio puro**: El servidor NO procesa audio, solo lo transmite
- **VAD nativo de GPT-4o**: La deteccion de voz y turn-taking la maneja OpenAI
- **Audio PCM16 a 24kHz**: Formato compatible con GPT-4o Realtime
- **Transcripcion con Whisper**: Para logging de las conversaciones

## Stack Tecnologico

- FastAPI
- Azure Communication Services
- Microsoft Teams (interoperability)
- OpenAI GPT-4o Realtime API
- Pydantic
- WebSockets

## Componentes a Implementar

1. Endpoint para iniciar llamadas salientes
2. Integracion con Azure Communication Services
3. Bridge WebSocket ACS <-> OpenAI Realtime
4. Logica de horarios para decidir canal de llamada (Teams vs Telefono)
5. Manejo de eventos de llamada (conectar, desconectar, errores)

## Documentacion de Referencia

- OpenAI Realtime API (WebSocket, SIP, WebRTC)
- Azure Communication Services con OpenAI Realtime

## Instalacion

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual (Windows)
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Configuracion

Crear archivo `.env` con las siguientes variables:

```
OPENAI_API_KEY=tu_api_key_de_openai
AZURE_COMMUNICATION_CONNECTION_STRING=tu_connection_string_de_acs
```

## Ejecucion

```bash
# Desarrollo
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Prueba de conexion con OpenAI Realtime (microfono local)
python test_realtime.py
```

## Documentacion de Endpoints

### Endpoints de Estado

#### GET /

Endpoint raiz para verificar que la API esta en funcionamiento.

**Respuesta:**
```json
{
  "status": "VoiceBot API Running",
  "acs_configured": true,
  "active_calls": 2
}
```

**Campos:**
- `status`: Estado del servidor
- `acs_configured`: Indica si Azure Communication Services esta configurado correctamente
- `active_calls`: Numero de llamadas activas en este momento

---

#### GET /health

Health check endpoint para monitoreo y load balancers.

**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-07T10:30:00"
}
```

---

### Endpoints de Gestion de Llamadas

#### POST /calls/outbound

Inicia una llamada saliente a un numero de telefono o usuario de Microsoft Teams.

**Request Body:**
```json
{
  "target_number": "+573001234567",
  "target_type": "phone"
}
```

**Parametros:**
- `target_number`: Numero de telefono (formato internacional con +) o email de usuario de Teams
- `target_type`: Tipo de destinatario
  - `"phone"`: Llamada a telefono tradicional via PSTN
  - `"teams"`: Llamada a usuario de Microsoft Teams

**Respuesta Exitosa:**
```json
{
  "call_id": "aHR0cHM6Ly9...",
  "status": "connecting",
  "target": "+573001234567",
  "started_at": "2026-01-07T10:30:00"
}
```

**Errores:**
- `503 Service Unavailable`: ACS no esta configurado o CALLBACK_URI no esta definido
- `500 Internal Server Error`: Error al crear la llamada en Azure

**Uso desde un Trigger:**

Este es el unico endpoint que necesitas llamar desde tu sistema de monitoreo o trigger. Todo el flujo posterior (conexion con OpenAI, manejo de audio, ejecucion de funciones DB2) se ejecuta automaticamente.

```python
import requests

# Detectar problema critico
response = requests.post(
    "http://tu-servidor:8000/calls/outbound",
    json={
        "target_number": "+573001234567",
        "target_type": "phone"
    }
)

call_info = response.json()
print(f"Llamada iniciada: {call_info['call_id']}")
```

---

#### GET /calls

Lista todas las llamadas activas en el sistema.

**Respuesta:**
```json
{
  "total": 2,
  "calls": [
    {
      "call_id": "abc123",
      "status": "connected",
      "target": "+573001234567",
      "started_at": "2026-01-07T10:30:00"
    },
    {
      "call_id": "def456",
      "status": "connecting",
      "target": "user@empresa.com",
      "started_at": "2026-01-07T10:35:00"
    }
  ]
}
```

**Uso:** Monitoreo de llamadas en curso, debugging, dashboards administrativos.

---

#### DELETE /calls/{call_id}

Termina una llamada especifica.

**Parametros de URL:**
- `call_id`: ID de la llamada a terminar

**Ejemplo:**
```bash
curl -X DELETE http://localhost:8000/calls/abc123
```

**Respuesta:**
```json
{
  "status": "call_ended",
  "call_id": "abc123"
}
```

**Errores:**
- `404 Not Found`: La llamada no existe o ya termino
- `503 Service Unavailable`: ACS no esta configurado

---

### Webhooks (Endpoints Internos)

#### POST /callbacks/acs

Webhook que recibe eventos de Azure Communication Services.

**IMPORTANTE:** Este endpoint NO debe ser llamado manualmente. Es llamado automaticamente por Azure cuando ocurren eventos en las llamadas.

**Configuracion Requerida:**

La URL publica de este endpoint debe estar configurada en la variable de entorno `CALLBACK_URI`. Para desarrollo local, usar ngrok:

```bash
ngrok http 8000
# Copiar la URL https generada
# Agregar al .env: CALLBACK_URI=https://tu-url-ngrok.io
```

**Eventos Procesados:**

| Evento | Descripcion | Accion Automatica |
|--------|-------------|-------------------|
| `CallConnected` | Llamada conectada exitosamente | Inicia conexion WebSocket con OpenAI Realtime |
| `CallDisconnected` | Llamada terminada | Cierra conexion con OpenAI y libera recursos |
| `MediaStreamingStarted` | Streaming de audio iniciado | Registra evento en logs |
| `MediaStreamingStopped` | Streaming de audio detenido | Registra evento en logs |
| `ParticipantsUpdated` | Cambios en participantes | Registra evento en logs |

**Formato de Request (ejemplo de Azure):**
```json
{
  "type": "Microsoft.Communication.CallConnected",
  "data": {
    "callConnectionId": "abc123"
  }
}
```

---

#### WS /ws/media

WebSocket que maneja el streaming de audio bidireccional entre Azure Communication Services y OpenAI Realtime.

**IMPORTANTE:** Este endpoint es llamado automaticamente por Azure cuando el media streaming esta activo. No requiere intervencion manual.

**Flujo de Datos:**

```
Usuario habla -> ACS captura -> /ws/media -> OpenAI Realtime
                                              |
Usuario escucha <- ACS reproduce <- /ws/media <- OpenAI genera audio
```

**Formato de Audio:**
- Entrada desde ACS: PCM 16-bit, 16kHz, mono
- Salida a OpenAI: PCM 16-bit, 24kHz, mono (con resampling si es necesario)

**Mensajes Recibidos:**

```json
{
  "kind": "AudioMetadata",
  "audioMetadata": {
    "callConnectionId": "abc123"
  }
}
```

```json
{
  "kind": "AudioData",
  "audioData": {
    "data": "base64_encoded_pcm_audio",
    "timestamp": "2026-01-07T10:30:00"
  }
}
```

---

### Endpoints de Utilidades

#### GET /utils/business-hours

Verifica si el momento actual esta dentro del horario laboral.

**Respuesta:**
```json
{
  "is_business_hours": true,
  "current_time": "2026-01-07T10:30:00",
  "recommendation": "teams"
}
```

**Campos:**
- `is_business_hours`: `true` si es horario laboral, `false` en caso contrario
- `current_time`: Timestamp actual del servidor
- `recommendation`: Canal recomendado para llamadas
  - `"teams"`: Usar Microsoft Teams (horario laboral)
  - `"phone"`: Usar telefono PSTN (fuera de horario)

**Logica de Horario Laboral:**
- Lunes a Viernes: 8:00 AM - 6:00 PM
- Sabados y Domingos: Fuera de horario

**Uso:** Decidir automaticamente el canal de comunicacion segun el horario.

```python
response = requests.get("http://localhost:8000/utils/business-hours")
data = response.json()

target_type = "teams" if data["is_business_hours"] else "phone"
```

---

## Flujo Completo de una Llamada

### 1. Inicio de Llamada (Manual o por Trigger)

Un sistema externo (trigger, cron job, alerta de monitoreo) detecta un problema y realiza un POST al endpoint `/calls/outbound`.

```python
requests.post("http://servidor:8000/calls/outbound", json={
    "target_number": "+573001234567",
    "target_type": "phone"
})
```

### 2. Azure Communication Services Inicia la Llamada

La API usa Azure Communication Services para marcar el numero. Azure gestiona la conexion telefonica.

### 3. Eventos de Azure (Automatico)

Cuando la llamada se conecta, Azure envia un evento `CallConnected` al webhook `/callbacks/acs`.

### 4. Conexion con OpenAI Realtime (Automatico)

Al recibir el evento `CallConnected`, el servidor establece automaticamente una conexion WebSocket con OpenAI Realtime API.

### 5. Configuracion de la Sesion (Automatico)

El servidor configura la sesion de OpenAI con:
- Instrucciones del sistema (desde `prompt.txt`)
- Voice model: `alloy`
- Server VAD activado para deteccion de voz
- Herramientas disponibles: funciones de consulta a DB2

### 6. Streaming de Audio Bidireccional (Automatico)

El audio fluye en tiempo real:
- Usuario habla -> ACS -> `/ws/media` -> OpenAI Realtime
- OpenAI genera respuesta -> `/ws/media` -> ACS -> Usuario escucha

### 7. Function Calling con DB2 (Automatico)

Cuando el usuario pregunta sobre el estado de la base de datos, OpenAI:
1. Detecta que necesita informacion
2. Llama automaticamente a funciones como `get_db2_tablespace_summary()`
3. Recibe datos en formato JSON
4. Procesa la informacion
5. Responde al usuario en lenguaje natural por voz

**Funciones DB2 Disponibles:**
- `get_db2_tablespace_usage`: Informacion detallada de tablespaces
- `get_db2_tablespace_summary`: Resumen conciso de problemas
- `get_db2_connection_health`: Verificacion de conexion a DB2
- `get_db2_database_size`: Metricas de tamano de base de datos

### 8. Finalizacion de Llamada (Manual o Automatica)

La llamada termina cuando:
- El usuario cuelga
- Se ejecuta `DELETE /calls/{call_id}`
- Timeout o error de conexion

Azure envia evento `CallDisconnected` y el servidor limpia todos los recursos automaticamente.

---

## Integracion con Sistemas de Monitoreo

Para integrar este sistema con tu monitoreo de DB2 o cualquier otro trigger:

```python
# ejemplo_trigger.py
import requests
from functions.db2_queries import get_db2_tablespace_summary

def check_and_call_if_critical():
    """Revisa DB2 y hace llamada si hay problemas criticos"""

    # Verificar estado de DB2
    result = get_db2_tablespace_summary()

    # Si hay problemas criticos, iniciar llamada
    if result.get("status") == "critical":
        response = requests.post(
            "http://localhost:8000/calls/outbound",
            json={
                "target_number": "+573001234567",
                "target_type": "phone"
            }
        )

        if response.status_code == 200:
            print(f"Llamada de alerta iniciada: {response.json()['call_id']}")
        else:
            print(f"Error al iniciar llamada: {response.text}")

# Ejecutar cada 5 minutos via cron
if __name__ == "__main__":
    check_and_call_if_critical()
```
