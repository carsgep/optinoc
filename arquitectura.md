# Arquitectura del Proyecto

Este documento explica el flujo real del proyecto y del PoC de telefonia para que sea facil entender quien habla con quien, en que orden, y cual es el papel de cada componente.

## Idea principal

La meta del proyecto es que una **voz generada por IA** converse por telefono con una **persona real**.

En el escenario del PoC de telefonia, la llamada queda asi:

1. En un extremo esta la **IA OPTI**, que vive en la aplicacion `FastAPI` y usa `OpenAI Realtime` para escuchar, razonar y responder con voz.
2. Esa IA no llama directamente al telefono. La llamada la orquesta **Azure Communication Services (ACS)**.
3. Como ACS necesita salir a la red telefonica tradicional, usa **Direct Routing** hacia un SBC.
4. En produccion ese SBC seria el **Cisco CUBE del cliente**.
5. En este PoC, ese SBC se simula con **FreePBX/Asterisk**.
6. Para que ese SBC simulado pueda llegar a un numero telefonico real, se usa **Twilio** como proveedor PSTN.

La idea, expresada en una sola linea, es esta:

```text
IA (OpenAI) <-> FastAPI <-> ACS <-> FreePBX/Asterisk <-> Twilio <-> Telefono real
```

## Componentes y su papel

### 1. FastAPI

Es la aplicacion principal del proyecto.

Su trabajo es:

- recibir la orden de iniciar una llamada en `POST /calls/outbound`
- pedirle a ACS que cree la llamada
- recibir eventos de ACS en `POST /callbacks/acs`
- manejar el WebSocket `WS /ws/media`
- abrir la sesion con `OpenAI Realtime`
- pasar audio entre ACS y OpenAI
- exponer herramientas del bot, por ejemplo consultas DB2

FastAPI no es la red telefonica. Es el cerebro de integracion.

### Uso de la API para Teams

Para iniciar llamadas a usuarios de Microsoft Teams se usa el endpoint:

```text
POST /calls/outbound
```

Importante:

- `target_type` debe ser `teams`
- debes enviar el `Object ID` del usuario en Teams, no el correo
- para un solo usuario usa `target_number`
- para varios usuarios usa `target_numbers`

### Consulta JSON para un solo usuario de Teams

```json
{
  "target_number": "494a9c73-2845-47d7-8a8b-f518095dbb2d",
  "target_type": "teams"
}
```

### Consulta JSON para multiples usuarios de Teams

```json
{
  "target_numbers": [
    "494a9c73-2845-47d7-8a8b-f518095dbb2d",
    "11111111-2222-3333-4444-555555555555",
    "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  ],
  "target_type": "teams"
}
```

### 2. OpenAI Realtime

Es el motor conversacional de la IA.

Su trabajo es:

- recibir el audio del humano
- transcribir e interpretar lo que la persona dice
- decidir la respuesta
- generar audio de voz sintetizada
- opcionalmente invocar funciones, por ejemplo consultas DB2

OpenAI no marca numeros telefonicos. Solo entiende y genera conversacion.

### 3. Azure Communication Services (ACS)

Es el motor de llamadas en la nube.

Su trabajo es:

- crear y controlar la llamada telefonica
- notificar eventos como `CallConnected` y `CallDisconnected`
- abrir el stream de audio hacia la aplicacion por WebSocket
- conectar el mundo del bot con el mundo telefonico
- en este PoC, enrutar llamadas por `Direct Routing` hacia el SBC simulado

ACS es quien "sostiene" la llamada. FastAPI no habla directo con Twilio ni con el telefono humano.

### 4. FreePBX / Asterisk

En el PoC actua como el **SBC simulado** que reemplaza temporalmente al Cisco CUBE real.

Su trabajo es:

- recibir llamadas SIP/TLS desde ACS
- aplicar reglas de ruteo telefonico
- reenviar la llamada al trunk de Twilio
- recibir llamadas desde Twilio y entregarlas al lado de ACS

En otras palabras, FreePBX/Asterisk hace de puente de telefonia entre Azure y la PSTN de Twilio.

### 5. Twilio

Twilio representa la salida a la red telefonica real.

Su trabajo es:

- aportar el numero de telefono del PoC
- recibir o originar trafico SIP con FreePBX/Asterisk
- convertir ese trafico en una llamada PSTN real hacia un celular o telefono humano

Twilio es el componente que hace posible que en el otro extremo haya un numero real.

### 6. Cloudflare Tunnel

Cloudflare se usa solo como apoyo de conectividad publica durante el PoC o desarrollo.

Su trabajo es:

- publicar el backend local para que ACS pueda llegar a `CALLBACK_URI`
- publicar el FQDN del SBC simulado para que ACS pueda alcanzarlo por `TCP 5061`
- evitar depender de una IP publica fija local mientras se prueba

Cloudflare no genera la llamada, no procesa audio y no actua como proveedor telefonico.

## Dos flujos distintos: control y audio

En este proyecto conviene separar la llamada en dos planos.

### A. Plano de control

Es el que dice cosas como:

- iniciar llamada
- llamada conectada
- llamada terminada
- abrir stream de media

Aqui intervienen principalmente:

- FastAPI
- ACS
- FreePBX/Asterisk
- Twilio

En SIP, esto corresponde a la senalizacion de la llamada.

### B. Plano de audio

Es la voz real de la conversacion.

Aqui intervienen principalmente:

- humano hablando por telefono
- Twilio
- FreePBX/Asterisk
- ACS
- FastAPI por `WS /ws/media`
- OpenAI Realtime

Este plano es el importante para que la IA escuche al humano y luego le responda con voz.

## Flujo logico completo de una llamada

El siguiente flujo describe el caso que quieres entender: un numero real humano habla con una voz IA.

### Paso 1. Un sistema dispara la llamada

Algo externo llama a la API:

```text
POST /calls/outbound
```

Ese trigger puede ser:

- una alerta de monitoreo
- una prueba manual
- otro sistema interno

### Paso 2. FastAPI solicita la llamada a ACS

La aplicacion usa el SDK de ACS para crear una llamada saliente.

ACS queda a cargo de la sesion telefonica y sabe a que `CALLBACK_URI` debe reportar eventos.

### Paso 3. ACS decide por donde sacar la llamada

Si la llamada es al mundo telefonico, ACS usa `Direct Routing`.

En el PoC, la ruta queda asi:

```text
ACS -> FreePBX/Asterisk -> Twilio -> numero real
```

En produccion, en vez de FreePBX/Asterisk seria el `Cisco CUBE` del cliente.

### Paso 4. FreePBX/Asterisk recibe la llamada desde ACS

FreePBX/Asterisk recibe la llamada SIP desde ACS por el trunk configurado para Azure.

Su rol aqui es:

- aceptar la llamada desde Azure
- aplicar las reglas de enrutamiento
- decidir que esa llamada debe salir por Twilio

### Paso 5. Twilio entrega la llamada al telefono real

Twilio toma la llamada que le paso FreePBX/Asterisk y la convierte en una llamada telefonica real hacia el numero del humano.

En este momento ya suena el celular o telefono del destinatario.

### Paso 6. ACS notifica a FastAPI que la llamada se conecto

Cuando el humano contesta, ACS envia eventos a:

```text
POST /callbacks/acs
```

Ejemplos:

- `CallConnected`
- `MediaStreamingStarted`
- `CallDisconnected`

Para que esto funcione, `CALLBACK_URI` debe ser publico. En desarrollo eso se resuelve con `Cloudflare Tunnel`.

### Paso 7. FastAPI abre la sesion con OpenAI Realtime

Al recibir `CallConnected`, la aplicacion inicializa la sesion conversacional del bot.

Aqui carga, por ejemplo:

- instrucciones desde `prompt.txt`
- configuracion de voz del asistente
- herramientas o funciones disponibles

### Paso 8. ACS abre el WebSocket de media con FastAPI

ACS envia y recibe audio usando:

```text
WS /ws/media
```

Ese WebSocket es el puente de audio entre la llamada de telefono y el motor de IA.

### Paso 9. El audio del humano viaja hacia la IA

Cuando el humano habla, el recorrido logico del audio es este:

```text
Humano -> Twilio -> FreePBX/Asterisk -> ACS -> /ws/media -> OpenAI Realtime
```

Interpretacion simple:

1. el humano habla por su telefono
2. Twilio recibe esa voz desde la red PSTN
3. FreePBX/Asterisk la recibe por SIP/RTP
4. ACS la mantiene dentro de la llamada en Azure
5. FastAPI la recibe por `WS /ws/media`
6. OpenAI la procesa y entiende que dijo la persona

### Paso 10. La respuesta de la IA vuelve al humano

Cuando OpenAI genera una respuesta, el recorrido logico de vuelta es este:

```text
OpenAI Realtime -> /ws/media -> ACS -> FreePBX/Asterisk -> Twilio -> Humano
```

Interpretacion simple:

1. OpenAI genera audio con la voz de OPTI
2. FastAPI lo pasa a ACS por el WebSocket de media
3. ACS lo inserta en la llamada telefonica
4. FreePBX/Asterisk lo enruta hacia Twilio
5. Twilio lo entrega al telefono real
6. la persona escucha una voz generada por IA

### Paso 11. Si la IA necesita datos, llama funciones

Durante la conversacion, OpenAI puede pedir informacion adicional, por ejemplo consultas DB2.

El flujo seria:

```text
Humano pregunta -> OpenAI decide usar una funcion -> FastAPI ejecuta la funcion -> OpenAI responde por voz
```

Esto permite que la IA no solo hable, sino que tambien responda con informacion real del sistema.

### Paso 12. La llamada termina

La llamada puede terminar porque:

- el humano cuelga
- la aplicacion la corta manualmente
- ocurre un error o timeout

Cuando eso pasa, ACS envia `CallDisconnected` y FastAPI libera los recursos de esa sesion.

## Diagrama simple del PoC

```text
                    Control de llamada + audio

Trigger/Alerta
     |
     v
FastAPI -----------------> ACS -----------------> FreePBX/Asterisk -----------------> Twilio -----------------> Humano
  |                           |                         |                                 |
  |                           |                         |                                 |
  +------ OpenAI Realtime <---+------ audio por WS -----+------ puente SIP/PSTN ----------+
```

## El papel de cada componente, en orden de la llamada

Si lo quieres pensar exactamente en el orden en que participan para llamar a un humano real desde una voz IA:

1. **FastAPI**
   Inicia la llamada y conecta la logica del bot.

2. **ACS**
   Crea y controla la llamada en la nube.

3. **FreePBX/Asterisk**
   Hace de SBC intermedio para Direct Routing en el PoC.

4. **Twilio**
   Saca la llamada a la red telefonica real y aporta el numero PSTN.

5. **Humano**
   Contesta y conversa.

6. **OpenAI Realtime**
   Aunque no esta en la ruta PSTN, es quien genera la voz IA y entiende al humano a traves del puente de audio montado por FastAPI y ACS.

7. **Cloudflare Tunnel**
   No es un participante de la llamada en si. Solo hace visibles hacia internet los endpoints locales necesarios para que el PoC funcione.

## Que cambia entre PoC y produccion

### En el PoC

- `FreePBX/Asterisk` simula al SBC del cliente
- `Twilio` simula la salida a la PSTN
- `Cloudflare Tunnel` ayuda a exponer servicios locales

### En produccion

- `Cisco CUBE` reemplaza a `FreePBX/Asterisk`
- la telefonia real del cliente puede reemplazar a `Twilio`
- normalmente se usa IP publica, DNS y certificado TLS del cliente en lugar de Cloudflare

La parte que no cambia es la idea central:

```text
IA <-> FastAPI <-> ACS <-> SBC <-> Telefonia real <-> Humano
```

## Reconstruccion del PoC paso a paso

Esta seccion esta pensada para tu situacion actual:

- necesitas crear un **Twilio nuevo**
- perdiste el servidor donde estaba **FreePBX/Asterisk**
- tambien perdiste la parte de **Kamailio** y configuracion del servidor
- **Cloudflare Tunnel** todavia lo tienes, pero puede requerir ajuste de hostnames o puertos

La idea de este checklist es reconstruir el PoC en el orden correcto para que no falte ninguna dependencia.

### 1. Definir la arquitectura que vas a reconstruir

Antes de tocar nada, define estas piezas:

1. Un servidor Linux nuevo para el SBC simulado.
2. `FastAPI` corriendo en tu entorno de aplicacion.
3. `Cloudflare Tunnel` para exponer:
   - el SBC hacia ACS
   - la API hacia `CALLBACK_URI`
4. Un numero nuevo en Twilio.
5. El recurso de `Azure Communication Services` con `Direct Routing`.

Si quieres reproducir el PoC mas cercano a lo documentado, piensa la ruta asi:

```text
FastAPI <-> ACS <-> Kamailio <-> FreePBX/Asterisk <-> Twilio <-> Humano
```

Si quieres una primera reconstruccion mas simple, puedes empezar sin Kamailio y dejar:

```text
FastAPI <-> ACS <-> FreePBX/Asterisk <-> Twilio <-> Humano
```

Luego agregas Kamailio y RTPEngine si vuelves a necesitar estabilizar senalizacion o audio.

### 2. Preparar el servidor nuevo

En el servidor nuevo necesitas, como minimo:

- Docker y Docker Compose
- `cloudflared`
- puertos disponibles para SIP, TLS y RTP
- si vas a usar Kamailio y RTPEngine: paquetes del sistema y acceso root

Puertos relevantes del PoC:

- `5060/tcp` para Twilio sobre SIP TCP
- `5061/tcp` para ACS sobre SIP TLS
- `10000-10100/udp` para RTP de FreePBX
- `20000-20100/udp` si usas RTPEngine
- `8080/tcp` y `8443/tcp` para administrar FreePBX

Si el servidor esta detras de firewall o NSG, abre esos puertos segun el escenario.

### 3. Levantar FreePBX/Asterisk otra vez

La base del PoC esta en `poc-sbc-simulado/docker-compose.yml`.

Ese contenedor expone precisamente los puertos necesarios:

- `5060` SIP
- `5061` SIP TLS
- `10000-10100` RTP
- `8080/8443` para la UI

Pasos:

1. Restaurar o clonar el repo en el servidor.
2. Ir a `poc-sbc-simulado/`.
3. Levantar:

```bash
docker compose up -d
```

4. Esperar varios minutos hasta que FreePBX termine de iniciar.
5. Entrar a la interfaz web en `http://<servidor>:8080` o por el acceso que uses localmente.
6. Completar el wizard inicial de FreePBX si aparece.

Objetivo de este paso: volver a tener un Asterisk funcional que haga de SBC simulado.

### 4. Decidir si vas a usar Kamailio desde el inicio

Segun `poc-sbc-simulado/ESTADO_POC.md`, Kamailio aparecio para mediar mejor la senalizacion y, junto con RTPEngine, ayudar con el problema de audio e ICE entre ACS y FreePBX.

Regla practica:

- si solo quieres reconstruir rapido y probar senalizacion basica, empieza con `FreePBX/Asterisk` solo
- si quieres acercarte al ultimo estado avanzado del PoC, reconstruye tambien `Kamailio + RTPEngine`

### 5. Si usas Kamailio, reconstruir su configuracion minima

La documentacion existente deja estas pistas:

- Kamailio escucha en `5061/tls` con `advertise <fqdn>:5061`
- tambien se documento `listen=udp:0.0.0.0:5062`
- FreePBX tenia un endpoint `kamailio` en `pjsip_custom.conf`

Configuracion minima a reconstruir:

1. Instalar Kamailio en el servidor.
2. Configurar `listen=tls:0.0.0.0:5061 advertise <tu-fqdn-sbc>:5061`.
3. Cargar certificado TLS valido para el FQDN publico.
4. Configurar el ruteo hacia FreePBX.
5. Verificar con:

```bash
sudo kamailio -c
sudo systemctl restart kamailio
sudo systemctl status kamailio
```

Si todavia no tienes esta parte lista, no bloquees el resto del PoC por Kamailio. Puedes dejarla para una segunda etapa.

### 6. Si usas RTPEngine, dejarlo listo desde el principio

La documentacion del PoC identifica que el audio con ACS falla por manejo de `ICE` entre ACS y FreePBX, y propone `RTPEngine` como solucion.

Lo minimo que deberias reconstruir es:

1. Instalar RTPEngine.
2. Configurar `listen-ng = 127.0.0.1:2223`.
3. Definir rango RTP, por ejemplo `20000-20100`.
4. Abrir esos puertos UDP en firewall.
5. Integrarlo en Kamailio con `rtpengine_manage(...)` en mensajes con SDP.

Si no vas a resolver audio todavia, puedes dejar RTPEngine para despues. Pero si tu objetivo es una llamada con audio bidireccional estable, esta pieza probablemente sera necesaria.

### 7. Reconfigurar Cloudflare Tunnel

Como todavia conservas Cloudflare, este paso es clave.

Necesitas exponer dos cosas distintas:

1. El FQDN del SBC para ACS.
2. La API de FastAPI para `CALLBACK_URI` y `/ws/media`.

Configuracion tipo:

```yaml
tunnel: sbc-poc
credentials-file: /home/tu-usuario/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: sbc-poc.tudominio.com
    service: tcp://localhost:5061
  - hostname: api-poc.tudominio.com
    service: http://localhost:8000
  - service: http_status:404
```

Si tu servidor cambio, revisa estas cosas:

- que el `hostname` siga existiendo en DNS dentro de Cloudflare
- que el tunnel siga apuntando al host correcto
- que `localhost:5061` realmente llegue al componente que expone TLS hacia ACS
- que `localhost:8000` sea tu API FastAPI

Si Twilio va a entrar por Cloudflare, recuerda que el PoC lo planteo sobre `TCP`, no `UDP`, porque Cloudflare Tunnel no soporta UDP.

En ese caso, una configuracion parecida a la de `AVANCES.md` seria:

```yaml
ingress:
  - hostname: sip.tudominio.com
    service: tcp://localhost:5060
  - hostname: sbc.tudominio.com
    service: tcp://localhost:5061
  - hostname: api.tudominio.com
    service: http://localhost:8000
  - service: http_status:404
```

### 8. Crear el nuevo Twilio

Ahora si, el proveedor PSTN.

Pasos en Twilio:

1. Crear o recuperar la cuenta Twilio.
2. Comprar un numero de prueba.
3. Crear un `Elastic SIP Trunk` nuevo.
4. Definir `Origination` para llamadas entrantes hacia tu SBC.
5. Definir `Termination` para llamadas salientes desde tu SBC hacia Twilio.
6. Asociar el numero Twilio al trunk.

La configuracion mas alineada con Cloudflare en este PoC es usar TCP:

```text
Origination URI: sip:sip.tudominio.com:5060;transport=tcp
```

Y para termination, Twilio te entregara algo tipo:

```text
<tu-trunk>.pstn.twilio.com
```

Tambien vas a crear credenciales:

- `TWILIO_SIP_USER`
- `TWILIO_SIP_PASS`

Y quedarte con estos datos:

- `TWILIO_PHONE_NUMBER`
- `TWILIO_SIP_DOMAIN`
- `TWILIO_SIP_USER`
- `TWILIO_SIP_PASS`

### 9. Configurar el trunk de Twilio en FreePBX

En FreePBX crea el trunk `twilio-trunk`.

Valores esperados:

- `Authentication: Outbound`
- `Registration: Send`
- `SIP Server: <tu-trunk>.pstn.twilio.com`
- `SIP Server Port: 5060`
- `Transport: TCP` si vas por Cloudflare
- `From Domain: <tu-trunk>.pstn.twilio.com`

El `Outbound CallerID` debe ser tu numero de Twilio.

Despues verifica en Asterisk:

```bash
docker exec freepbx-sbc asterisk -rx "pjsip show registrations"
```

Aqui deberias ver si el registro contra Twilio quedo bien.

### 10. Configurar el lado ACS en FreePBX o en Kamailio

Aqui depende de tu topologia final.

#### Opcion A. Sin Kamailio

FreePBX recibe directamente desde ACS:

- trunk `acs-trunk`
- `SIP Server: sip.pstnhub.microsoft.com`
- `SIP Server Port: 5061`
- `Transport: TLS`
- `Authentication: None`
- `Registration: None`
- `From Domain: <tu-fqdn-publico-del-sbc>`
- `Match (Permit): 52.112.0.0/14,52.120.0.0/14`

#### Opcion B. Con Kamailio

Kamailio recibe desde ACS y luego enruta internamente a FreePBX.

En ese caso debes reconstruir:

- el listener TLS publico en Kamailio
- el endpoint `kamailio` en FreePBX
- el ruteo de Kamailio hacia Asterisk

Esta opcion es la mas cercana al estado avanzado del PoC.

### 11. Reconfigurar las rutas en FreePBX

Necesitas dos clases de rutas.

#### Ruta entrante desde ACS

Sirve para que una llamada que llegue desde Azure entre al contexto correcto.

Configura una `Inbound Route` como minimo para capturar esas llamadas.

#### Ruta saliente hacia PSTN por Twilio

Sirve para que lo que entra desde ACS pueda salir al numero real por Twilio.

Configura una `Outbound Route` con patrones como:

- `57XXXXXXXXXX`
- `1XXXXXXXXXX`

Y usa `twilio-trunk` en la secuencia.

### 12. Registrar nuevamente el SBC en Azure ACS

En tu recurso ACS debes volver a dejar el SBC apuntando al nuevo servidor o al nuevo hostname efectivo.

Pasos:

1. Ir a `Direct Routing`.
2. Crear o actualizar el `Session Border Controller`.
3. Usar:
   - `FQDN: <tu-fqdn-publico>`
   - `Port: 5061`
4. Crear o revisar `Voice Routes`.
5. Asociar el patron de numeros al SBC.

Si el hostname cambio, aqui lo tienes que actualizar si o si.

Despues espera hasta que el estado del SBC pase a `Online`.

### 13. Reconfigurar la API FastAPI

En `main.py` las variables mas importantes son:

- `ACS_CONNECTION_STRING`
- `CALLBACK_URI`
- `OPENAI_API_KEY`

Si estas reconstruyendo por completo, revisa el `.env` y deja por lo menos:

```bash
ACS_CONNECTION_STRING=endpoint=https://xxx.communication.azure.com/;accesskey=xxx
CALLBACK_URI=https://api-poc.tudominio.com
OPENAI_API_KEY=sk-xxx
```

Si la llamada sera PSTN desde ACS, tambien revisa cualquier variable asociada al caller ID que uses en tu despliegue.

### 14. Verificar que Cloudflare soporte el callback de ACS

Antes de hacer pruebas de voz, verifica estas URLs:

- `https://api-poc.tudominio.com/health`
- `https://api-poc.tudominio.com/test/websocket`

Y valida logicamente que:

- `CALLBACK_URI/callbacks/acs` sea publico
- `CALLBACK_URI/ws/media` sea accesible como WebSocket

Sin esto, ACS puede crear la llamada pero no podra notificar eventos o abrir el stream de audio.

### 15. Pruebas en el orden correcto

Haz las pruebas en esta secuencia para aislar errores.

#### Prueba 1. FreePBX vivo

```bash
docker compose ps
docker compose logs -f freepbx
```

#### Prueba 2. Registro de Twilio

```bash
docker exec freepbx-sbc asterisk -rx "pjsip show registrations"
```

#### Prueba 3. Tunnel de Cloudflare

```bash
cloudflared tunnel info sbc-poc
```

#### Prueba 4. SBC visible desde ACS

Verificar en Azure Portal que el SBC quede `Online`.

#### Prueba 5. API visible

```bash
curl https://api-poc.tudominio.com/health
```

#### Prueba 6. Llamada Twilio -> FreePBX

Llama al numero Twilio desde tu celular. Primero valida que la llamada llegue al PBX.

#### Prueba 7. Llamada ACS -> FreePBX

Lanza la llamada desde tu API:

```bash
curl -X POST http://localhost:8000/calls/outbound \
  -H "Content-Type: application/json" \
  -d '{"target_number": "+573001234567", "target_type": "phone"}'
```

#### Prueba 8. Audio bidireccional

Solo despues de que la llamada conecte, revisa si existe audio en ambos sentidos. Si hay senalizacion pero no audio, vuelve a revisar:

- RTP
- ICE
- SRTP
- Kamailio
- RTPEngine

### 16. Orden recomendado de reconstruccion

Si quieres la version mas pragmatica, reconstruyelo asi:

1. Levantar `FastAPI`.
2. Levantar `FreePBX/Asterisk`.
3. Reconfigurar `Cloudflare` para SBC y API.
4. Crear `Twilio` nuevo y asociar el numero.
5. Configurar trunk `Twilio` en FreePBX.
6. Registrar el SBC en `ACS`.
7. Probar senalizacion de llamada.
8. Solo despues, reconstruir `Kamailio + RTPEngine` si el audio falla.

Ese orden reduce el riesgo de intentar depurar audio cuando aun no esta resuelta la conectividad basica.

### 17. Checklist minimo de datos que debes recuperar o volver a crear

- FQDN publico del SBC
- FQDN publico de la API
- tunnel de Cloudflare y su `credentials-file`
- nuevo numero de Twilio
- nuevo SIP trunk de Twilio
- usuario y clave SIP de Twilio
- `ACS_CONNECTION_STRING`
- `CALLBACK_URI`
- `OPENAI_API_KEY`
- certificado TLS del hostname publico del SBC
- reglas de firewall o NSG del nuevo servidor

### 18. Advertencia importante sobre el estado real del PoC

Segun la documentacion existente, el PoC llego a tener:

- senalizacion ACS -> FreePBX funcionando
- bridge FreePBX -> Twilio funcionando
- llamada llegando al telefono real
- problema pendiente en audio bidireccional por ICE

Eso significa que reconstruir `Twilio + FreePBX + Cloudflare + ACS` puede devolverte rapidamente la llamada conectada, pero no garantiza por si solo el audio estable. Si reaparece el mismo problema, el siguiente frente a reconstruir sera `Kamailio + RTPEngine`.

## Resumen corto

- **OpenAI** pone la inteligencia y la voz.
- **FastAPI** integra toda la logica.
- **ACS** sostiene la llamada y el stream de audio.
- **FreePBX/Asterisk** hace de SBC en el PoC.
- **Twilio** conecta con el numero telefonico real.
- **Cloudflare** solo expone endpoints locales para pruebas.

Si quieres, el siguiente paso puede ser crear una segunda version de este documento con un diagrama ASCII mas detallado separando claramente `senalizacion SIP` y `media/audio`.
