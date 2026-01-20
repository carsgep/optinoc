# Optinoc BOCC Realtime - Contexto para Claude

## Descripcion del Proyecto

Sistema de llamadas automatizadas con IA que actua como puente bidireccional entre Azure Communication Services (ACS) y OpenAI Realtime API. Permite que un asistente de voz llamado **OPTI** realice llamadas automaticas para monitoreo NOC/SOC.

## Arquitectura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────────┐
│   Trigger       │────>│   FastAPI        │<───>│   OpenAI Realtime API   │
│   Externo       │     │   Server         │     │   gpt-realtime-mini     │
└─────────────────┘     └────────┬─────────┘     └─────────────────────────┘
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
       ┌─────────────┐                   ┌─────────────────────┐
       │   Microsoft │                   │   Cisco (Direct     │
       │   Teams     │                   │   Routing via ACS)  │
       └─────────────┘                   └─────────────────────┘
```

## Stack Tecnologico

| Componente | Tecnologia |
|------------|------------|
| Framework Web | FastAPI |
| Llamadas | Azure Communication Services |
| IA Conversacional | OpenAI Realtime API (`gpt-realtime-mini-2025-12-15`) |
| Validacion | Pydantic |
| Colaboracion | Microsoft Teams |
| Telefonia fuera de horario | Cisco (Direct Routing via ACS) |
| Base de datos | DB2 (consultas NOC/SOC) |

## Estructura del Proyecto

```
optinoc-bocc-realtime/
├── main.py                 # Servidor FastAPI principal
├── prompt.txt              # System prompt para OPTI
├── requirements.txt        # Dependencias Python
├── CLAUDE.md               # Este archivo
├── README.md               # Documentacion general
├── .env                    # Variables de entorno (no versionado)
├── functions/              # Funciones para OpenAI function calling
│   ├── __init__.py
│   ├── functions.py        # Registro de funciones
│   └── db2_queries.py      # Consultas a DB2
├── db/                     # Configuracion de base de datos
├── infra_optinoc/          # Infraestructura Terraform
├── agents/                 # Documentacion de agentes especializados
│   ├── claude.md           # Contexto general
│   └── azure-communication-service/
│       ├── context.md      # Contexto del agente ACS
│       ├── SKILLS.md       # Comandos y metodos de ACS
│       └── PRICING.md      # Precios de ACS
└── .claude/
    ├── settings.local.json # Configuracion local de Claude
    └── commands/           # Comandos personalizados
        └── acs.md          # Comando para agente ACS
```

## Escenarios de Llamada

| Escenario | Cuando | Canal |
|-----------|--------|-------|
| Horario laboral | Lunes-Viernes 8:00-18:00 | Microsoft Teams |
| Fuera de horario | Noches, fines de semana | Cisco (Direct Routing via ACS) |

**Nota:** Fuera de horario laboral se utiliza la infraestructura telefonica Cisco existente del cliente, integrada con ACS mediante Direct Routing.

## Endpoints Principales

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

## Variables de Entorno

```bash
# Obligatorias
ACS_CONNECTION_STRING=endpoint=https://xxx.communication.azure.com/;accesskey=xxx
CALLBACK_URI=https://tu-url.trycloudflare.com
OPENAI_API_KEY=sk-xxx

# Para llamadas PSTN/Cisco Direct Routing
ACS_PHONE_NUMBER=+1XXXXXXXXXX

# Opcionales
COGNITIVE_SERVICES_ENDPOINT=https://xxx.cognitiveservices.azure.com
```

## Comandos de Desarrollo

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Exponer con cloudflared (desarrollo)
cloudflared tunnel --url http://localhost:8000
```

---

## Agentes Especializados

Este proyecto cuenta con agentes especializados que puedes activar para tareas especificas.

### Agente: Azure Communication Service

**Comando:** `/project:acs`

**Descripcion:** Agente especializado en Azure Communication Services Call Automation. Tiene conocimiento profundo sobre:

- Creacion y manejo de llamadas (Teams, Direct Routing/Cisco)
- Media streaming bidireccional
- Grabacion de llamadas
- Text-to-Speech y Speech-to-Text
- Reconocimiento DTMF
- Eventos de callback
- Direct Routing para integracion con Cisco

**Cuando usarlo:**
- Implementar nuevas funcionalidades de llamadas
- Configurar media streaming
- Resolver problemas con ACS
- Agregar soporte para Teams interop
- Configurar Direct Routing con Cisco

**Archivos de referencia:**
- `agents/azure-communication-service/context.md` - Contexto del proyecto
- `agents/azure-communication-service/SKILLS.md` - Todos los comandos y metodos
- `agents/azure-communication-service/PRICING.md` - Precios de referencia

---

## Consideraciones Tecnicas

### Modelo de IA

- **Modelo:** `gpt-realtime-mini-2025-12-15`
- **API:** OpenAI Realtime API via WebSocket

### Formato de Audio

| Servicio | Formato | Sample Rate |
|----------|---------|-------------|
| ACS (default) | PCM 16-bit mono | 16 kHz |
| ACS (opcional) | PCM 16-bit mono | 24 kHz |
| OpenAI Realtime | PCM 16-bit mono | 24 kHz |

### OPTI - El Asistente de Voz

El asistente se llama **OPTI** y tiene comandos de control por voz:

- **Silenciar:** "OPTI silencio", "OPTI espera"
- **Reactivar:** "OPTI habla", "OPTI continua"

El prompt del sistema esta en `prompt.txt`.

### Function Calling

OPTI tiene acceso a funciones para consultar DB2:
- `funcion_llamada_db2` - Consultas a la base de datos NOC/SOC
- `set_bot_muted` - Control de silencio del bot

---

## Tareas Pendientes

### Alta Prioridad
1. Completar flujo de audio bidireccional
2. Configurar Media Streaming con `enable_bidirectional=True`
3. Implementar llamadas entrantes

### Media Prioridad
4. Integracion con Teams (Teams Interoperability)
5. Integracion con Cisco via Direct Routing
6. Grabacion de llamadas

### Baja Prioridad
7. Reconocimiento DTMF
8. Metricas y Logging avanzado

---

## Referencias

- [Azure Communication Services - Call Automation](https://learn.microsoft.com/en-us/azure/communication-services/concepts/call-automation/call-automation)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- [ACS Direct Routing](https://learn.microsoft.com/en-us/azure/communication-services/concepts/telephony/direct-routing-infrastructure)
- [Audio Streaming Quickstart](https://learn.microsoft.com/en-us/azure/communication-services/how-tos/call-automation/audio-streaming-quickstart)
