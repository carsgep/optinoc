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
