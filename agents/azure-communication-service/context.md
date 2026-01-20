# Azure Communication Service Agent - Contexto del Proyecto

## Objetivo del Agente

Este agente tiene como objetivo generar y modificar codigo relacionado con Azure Communication Services (ACS) Call Automation para el proyecto **Optinoc BOCC Realtime**. Al inicializarse como este agente, tendras acceso a todos los comandos, metodos y patrones documentados en `SKILLS.md`.

---

## Descripcion del Proyecto

**Optinoc BOCC Realtime** es un sistema de llamadas automatizadas con IA que actua como puente bidireccional entre:

1. **Azure Communication Services (ACS)** - Manejo de llamadas de voz
2. **OpenAI GPT-4o Realtime API** - Procesamiento de conversacion con IA

### Arquitectura General

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Trigger       │────>│   FastAPI        │<───>│   OpenAI        │
│   Externo       │     │   Server         │     │   Realtime API  │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                               │
                               │ WebSocket
                               │ Bidireccional
                               ▼
                        ┌──────────────────┐
                        │   Azure          │
                        │   Communication  │
                        │   Services       │
                        └────────┬─────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                                 ▼
       ┌─────────────┐                   ┌─────────────┐
       │   Microsoft │                   │   PSTN /    │
       │   Teams     │                   │   Cisco SIP │
       └─────────────┘                   └─────────────┘
```

---

## Escenarios de Llamada

### Escenario 1: Horario Laboral → Llamada a Teams

Cuando es horario habill (Lunes-Viernes, 8:00-18:00):
- Se llama al usuario via Microsoft Teams
- Requiere Teams Interoperability habilitado en ACS
- Usa `MicrosoftTeamsUserIdentifier`

### Escenario 2: Fuera de Horario → Llamada PSTN/Cisco

Cuando es fuera de horario laboral o fines de semana:
- Se llama al tecnico responsable por telefono
- Puede usar PSTN directo (numero ACS) o SIP trunk a Cisco
- Usa `PhoneNumberIdentifier`

---

## Stack Tecnologico

| Componente | Tecnologia |
|------------|------------|
| Framework Web | FastAPI |
| Llamadas | Azure Communication Services |
| IA Conversacional | OpenAI GPT-4o Realtime API |
| Validacion | Pydantic |
| Colaboracion | Microsoft Teams |
| Telefonia | PSTN / Cisco SIP |

---

## Estructura del Proyecto Actual

```
optinoc-bocc-realtime/
├── main.py              # Servidor FastAPI principal
├── prompt.txt           # System prompt para la IA
├── requirements.txt     # Dependencias Python
├── .env                 # Variables de entorno (no versionado)
└── agents/
    ├── claude.md        # Contexto general del proyecto
    └── azure-communication-service/
        ├── SKILLS.md    # Comandos y servicios de ACS
        └── context.md   # Este archivo
```

---

## Endpoints Actuales

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| GET | `/` | Estado del servidor |
| GET | `/health` | Health check |
| POST | `/calls/outbound` | Iniciar llamada saliente |
| GET | `/calls` | Listar llamadas activas |
| DELETE | `/calls/{call_id}` | Terminar llamada |
| POST | `/callbacks/acs` | Webhook para eventos ACS |
| WS | `/ws/media` | WebSocket para audio streaming |
| GET | `/utils/business-hours` | Verificar horario laboral |

---

## Tareas Pendientes / Por Implementar

### Alta Prioridad

1. **Completar flujo de audio bidireccional**
   - Recibir audio de ACS via WebSocket
   - Resampling de audio si es necesario (16kHz ↔ 24kHz)
   - Enviar audio de respuesta de OpenAI hacia ACS

2. **Configurar Media Streaming con Bidireccional**
   - Usar `MediaStreamingOptions` con `enable_bidirectional=True`
   - Definir formato de audio adecuado (PCM16K o PCM24K)

3. **Implementar llamadas entrantes**
   - Configurar EventGrid para recibir eventos `IncomingCall`
   - Endpoint para `answer_call()`

### Media Prioridad

4. **Integracion con Teams**
   - Habilitar Teams Interoperability en ACS
   - Probar llamadas a usuarios de Teams

5. **Integracion con Cisco SIP**
   - Configurar SIP trunk entre ACS y Cisco
   - Pruebas de llamadas via infraestructura telefonica

6. **Grabacion de llamadas**
   - Implementar `start_recording()` / `stop_recording()`
   - Almacenar grabaciones en Azure Blob Storage

### Baja Prioridad

7. **Reconocimiento DTMF**
   - Menus interactivos con tonos
   - Fallback cuando STT no funciona

8. **Metricas y Logging**
   - Tracking de duracion de llamadas
   - Logs estructurados para debugging

---

## Variables de Entorno Necesarias

```bash
# Obligatorias
ACS_CONNECTION_STRING=endpoint=https://xxx.communication.azure.com/;accesskey=xxx
CALLBACK_URI=https://tu-ngrok-url.ngrok.io
OPENAI_API_KEY=sk-xxx

# Para llamadas PSTN
ACS_PHONE_NUMBER=+1XXXXXXXXXX

# Opcionales
COGNITIVE_SERVICES_ENDPOINT=https://xxx.cognitiveservices.azure.com
```

---

## Flujo de Audio Actual

```
1. POST /calls/outbound
   ↓
2. acs_client.create_call() → callback_url
   ↓
3. ACS conecta la llamada
   ↓
4. Evento CallConnected → /callbacks/acs
   ↓
5. connect_to_openai_realtime(call_id)
   ↓
6. WebSocket a OpenAI establecido
   ↓
7. [PENDIENTE] Audio de ACS → /ws/media → OpenAI
   ↓
8. [PENDIENTE] Respuesta OpenAI → /ws/media → ACS
```

---

## Consideraciones Tecnicas

### Formato de Audio

| Servicio | Formato | Sample Rate |
|----------|---------|-------------|
| ACS (default) | PCM 16-bit mono | 16 kHz |
| ACS (opcional) | PCM 16-bit mono | 24 kHz |
| OpenAI Realtime | PCM 16-bit mono | 24 kHz |

**Nota:** Puede requerir resampling de 16kHz a 24kHz.

### WebSocket Headers de ACS

ACS incluye estos headers en la conexion WebSocket:
- `x-ms-call-correlation-id`: ID de correlacion
- `x-ms-call-connection-id`: ID de conexion de llamada

### Deteccion de Actividad de Voz (VAD)

GPT-4o Realtime maneja VAD internamente con configuracion:
```python
"turn_detection": {
    "type": "server_vad",
    "threshold": 0.5,
    "prefix_padding_ms": 300,
    "silence_duration_ms": 500
}
```

---

## Comandos de Desarrollo

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Exponer con ngrok (para desarrollo)
ngrok http 8000

# Ver logs de ngrok
ngrok http 8000 --log stdout
```

---

## Como Usar Este Agente

Cuando necesites trabajar con Azure Communication Services en este proyecto:

1. **Inicializa el agente:**
   > "Inicializate como el agente de azure-communication-service"

2. **Solicita tareas especificas:**
   - "Implementa el flujo de media streaming bidireccional"
   - "Agrega soporte para llamadas entrantes"
   - "Configura grabacion de llamadas"

3. **Consulta comandos:**
   - Revisa `SKILLS.md` para ver todos los metodos disponibles
   - Los ejemplos de codigo estan listos para copiar y adaptar

---

## Referencias

- [Azure Communication Services - Call Automation](https://learn.microsoft.com/en-us/azure/communication-services/concepts/call-automation/call-automation)
- [SDK Python - Call Automation](https://learn.microsoft.com/en-us/python/api/overview/azure/communication-callautomation-readme)
- [Audio Streaming Quickstart](https://learn.microsoft.com/en-us/azure/communication-services/how-tos/call-automation/audio-streaming-quickstart)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
