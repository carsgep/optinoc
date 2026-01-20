Este proyecto implementa un servidor FastAPI que actua como puente bidireccional entre Azure Communication Services (ACS) y OpenAI Realtime API (modelo: `gpt-realtime-mini-2025-12-15`) para conversaciones de voz en tiempo real. El sistema soporta dos escenarios principales: (1) llamadas salientes a usuarios de Microsoft Teams mediante Teams interoperability de ACS, y (2) llamadas VoIP a traves de la infraestructura telefonica Cisco de la empresa usando Direct Routing de ACS. El servidor gestiona WebSockets bidireccionales para transmitir audio PCM entre ACS y OpenAI Realtime, donde toda la logica de conversacion, deteccion de actividad de voz (VAD), turn-taking y generacion de respuestas es manejada nativamente por el modelo. La arquitectura es simple, escalable y enfocada en actuar como relay de audio sin procesamiento intermedio innecesario, permitiendo que triggers externos inicien llamadas automaticas donde un asistente IA (OPTI) interactue naturalmente con los usuarios tanto en Teams como en telefonos tradicionales a traves de Cisco.

## Stack

- FastAPI
- Azure Communication Services
- Microsoft Teams
- Pydantic
- OpenAI Realtime API (`gpt-realtime-mini-2025-12-15`)
- Cisco (Direct Routing via ACS)

## Escenarios de Llamada

| Escenario | Cuando | Canal |
|-----------|--------|-------|
| Horario laboral | Lunes-Viernes 8:00-18:00 | Microsoft Teams |
| Fuera de horario | Noches, fines de semana | Cisco via Direct Routing (ACS) |

## Desarrollo

- **Tunnel:** cloudflared (no ngrok)
- **Servidor:** uvicorn main:app --reload --host 0.0.0.0 --port 8000 