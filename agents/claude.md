Este proyecto implementa un servidor FastAPI que actúa como puente bidireccional entre Azure Communication Services (ACS) y GPT-4o Realtime API de OpenAI para conversaciones de voz en tiempo real. El sistema debe soportar dos escenarios principales: (1) llamadas salientes a usuarios de Microsoft Teams mediante Teams interoperability de ACS, y (2) llamadas VoIP a través de la infraestructura telefónica Cisco de la empresa usando SIP trunking. El servidor gestiona WebSockets bidireccionales para transmitir audio PCM entre ACS y GPT-4o Realtime, donde toda la lógica de conversación, detección de actividad de voz (VAD), turn-taking y generación de respuestas es manejada nativamente por GPT-4o. La arquitectura debe ser simple, escalable y enfocada en actuar como relay de audio sin procesamiento intermedio innecesario, permitiendo que triggers externos inicien llamadas automáticas donde un asistente IA interactúe naturalmente con los usuarios tanto en Teams como en teléfonos tradicionales a través de Cisco.


Stack:
FastAPI
Azure Communication Service 
Teams 
Pydantic


Consideraciones:
La idea es que dependiendo del día y la hora, si es un horario hábil para la empresa, llamar a las personas por teams. 
Pero si no es un día o tiempo hábil habría que llamar por teléfono a los técnicos responsables. 