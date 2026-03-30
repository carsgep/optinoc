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
                               │ WebSocket Bidireccional
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
├── CLAUDE.md               # Este archivo - contexto del proyecto
├── README.md               # Documentacion general
├── .env                    # Variables de entorno (no versionado)
│
├── functions/              # Funciones para OpenAI function calling
│   ├── __init__.py
│   ├── functions.py        # Registro de funciones
│   └── db2_queries.py      # Consultas a DB2
│
├── db/                     # Configuracion de base de datos
├── infra_optinoc/          # Infraestructura Terraform
│
├── .claude/
│   ├── settings.local.json # Configuracion local de Claude
│   └── agents/             # DEFINICIONES de agentes especializados
│       └── azure-communication-service.md
│
└── agents/                 # DOCUMENTACION de agentes
    └── azure-communication-service/
        ├── CONTEXT.md      # Arquitectura y contexto
        ├── SKILLS.md       # Comandos y metodos
        ├── HISTORY.md      # Historial y decisiones
        ├── PRICING.md      # Precios de referencia
        └── scripts/        # Scripts de utilidad
            ├── start-server.sh
            ├── start-tunnel.sh
            ├── test-call.sh
            ├── list-calls.sh
            └── check-status.sh
```

---

## Agentes Especializados

Este proyecto utiliza agentes especializados para tareas especificas. La estructura de agentes es:

- **`.claude/agents/`** - Contiene las definiciones de los agentes (archivos .md con frontmatter)
- **`agents/`** - Contiene la documentacion detallada de cada agente

### Como Funcionan los Agentes

1. El archivo en `.claude/agents/<nombre>.md` define el agente con frontmatter (name, description, model, color)
2. El agente lee la documentacion de `agents/<nombre>/` al inicializarse
3. Los scripts en `agents/<nombre>/scripts/` proporcionan utilidades ejecutables

### Agente: Azure Communication Service

**Ubicacion:** `.claude/agents/azure-communication-service.md`

**Descripcion:** Agente especializado en Azure Communication Services Call Automation.

**Capacidades:**
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

**Documentacion del agente:**

| Archivo | Contenido |
|---------|-----------|
| `agents/azure-communication-service/CONTEXT.md` | Arquitectura y contexto del proyecto |
| `agents/azure-communication-service/SKILLS.md` | Comandos, metodos y ejemplos de codigo |
| `agents/azure-communication-service/HISTORY.md` | Historial del proyecto y decisiones |
| `agents/azure-communication-service/PRICING.md` | Precios de referencia de ACS |
| `agents/azure-communication-service/scripts/` | Scripts de utilidad (.sh) |

---

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

O usar los scripts del agente:
```bash
./agents/azure-communication-service/scripts/start-server.sh
./agents/azure-communication-service/scripts/start-tunnel.sh
```

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

## PoC: SBC Simulado (Direct Routing)

**IMPORTANTE:** Hay un PoC en progreso para simular la infraestructura del cliente (Cisco CUBE) y probar Direct Routing con Azure ACS.

### Documentacion del PoC

| Archivo | Descripcion |
|---------|-------------|
| `poc-sbc-simulado/ESTADO_POC.md` | **Estado actual y plan de accion** |
| `poc-sbc-simulado/AVANCES.md` | Avances detallados |
| `poc-sbc-simulado/README.md` | Guia de instalacion |
| `poc-sbc-simulado/docker-compose.yml` | Configuracion Docker |

### Infraestructura del Cliente Real

| Componente | Version | Administrador |
|------------|---------|---------------|
| Cisco CUCM | 12.5.1.13900-152 | Proveedor telefonia |
| Cisco CUBE | IOS XE 16.09.01 (ASR1000) | Banco de Occidente |

### Estado Actual del PoC

- [x] FreePBX corriendo en Docker (simula CUBE)
- [x] Twilio configurado (simula PSTN del cliente)
- [x] Llamadas entrantes funcionan (via bore.pub)
- [ ] VM en Azure con IP publica
- [ ] Certificado TLS (Let's Encrypt)
- [ ] Azure ACS Direct Routing configurado

### Siguiente Paso

Crear VM en Azure y configurar Direct Routing. Ver `poc-sbc-simulado/ESTADO_POC.md` para el plan completo.

### Documentacion Relacionada al Cliente

| Archivo | Descripcion |
|---------|-------------|
| `guia_reunion_cisco_cube_acs.md` | Guia tecnica completa para reunion con cliente |
| `informacion_cisco_sbc_acs.md` | Requisitos tecnicos Direct Routing |
| `cuestionario_tecnico_banco.md` | Preguntas para el equipo tecnico del banco |
| `requerimientos_banco_occidente.md` | Requerimientos formales del proyecto |

---

## Referencias

- [Azure Communication Services - Call Automation](https://learn.microsoft.com/en-us/azure/communication-services/concepts/call-automation/call-automation)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- [ACS Direct Routing](https://learn.microsoft.com/en-us/azure/communication-services/concepts/telephony/direct-routing-infrastructure)
- [Audio Streaming Quickstart](https://learn.microsoft.com/en-us/azure/communication-services/how-tos/call-automation/audio-streaming-quickstart)
