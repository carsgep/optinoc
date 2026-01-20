# Documento de Requerimientos Técnicos
## Implementación de Optinoc VoiceBot para Banco de Occidente

**Preparado por:** Optimize IT
**Fecha:** Enero 2026

---

## Introducción

El presente documento describe los requerimientos técnicos e infraestructura que el Banco de Occidente debe proveer para la correcta implementación y operación de la solución Optinoc VoiceBot. Este sistema permite realizar llamadas automatizadas a usuarios de Microsoft Teams con capacidades de inteligencia artificial conversacional, integrándose con los sistemas de monitoreo NOC/SOC del banco para notificación proactiva de incidentes.

---

## 1. Licenciamiento de Microsoft Teams Phone

Para que el agente Optinoc pueda realizar llamadas a usuarios del banco a través de Microsoft Teams, cada usuario que deba recibir llamadas del sistema requiere una licencia de **Microsoft Teams Phone Standard**. Esta licencia habilita la funcionalidad de Enterprise Voice en el perfil del usuario, lo cual es un prerrequisito indispensable para que Azure Communication Services pueda establecer comunicación bidireccional de voz con dicho usuario. Sin esta licencia, el intento de llamada será rechazado por Microsoft con un error de permisos. La cantidad de licencias dependerá del número de operadores, ingenieros o personal de guardia que el banco desee incluir en el sistema de notificaciones automatizadas.

---

## 2. Máquina Virtual para Hospedaje del Servicio

Se requiere aprovisionar una máquina virtual dentro de la suscripción de Azure del Banco de Occidente con las siguientes características mínimas: 2 vCPUs, 4 GB de memoria RAM y un disco SSD de 64 GB (configuración equivalente a Azure B2s). Esta máquina virtual hospedará el servicio Optinoc, el cual consiste en una aplicación Python con FastAPI que gestiona las conexiones WebSocket tanto con Azure Communication Services como con la API de OpenAI Realtime. El sistema operativo recomendado es Ubuntu Server 22.04 LTS. Adicionalmente, el almacenamiento debe contemplar espacio suficiente para guardar los logs de las llamadas, transcripciones generadas por el sistema y posibles grabaciones de audio si el banco lo requiere para cumplimiento normativo. Se recomienda considerar un disco adicional o aumentar el tamaño según las políticas de retención de datos del banco.

---

## 3. Azure Communication Services en el Tenant del Banco

Es fundamental que el recurso de **Azure Communication Services (ACS)** sea creado directamente en el tenant de Azure del Banco de Occidente. Este servicio es el componente que establece las llamadas hacia los usuarios de Microsoft Teams y gestiona el streaming de audio bidireccional. El recurso de ACS debe configurarse con la federación hacia Microsoft Teams habilitada, lo cual requiere que un administrador de Teams del banco ejecute comandos de PowerShell para autorizar el Immutable Resource ID de ACS como fuente confiable de llamadas. Si el recurso de ACS está en un tenant diferente al de Teams, la federación no funcionará y las llamadas serán rechazadas. Los costos asociados a ACS incluyen VoIP Calling, Audio Streaming y potencialmente Direct Routing si se desea integración con telefonía PSTN.

---

## 4. Configuración de Permisos en Microsoft Teams

Un administrador con privilegios de Teams Administrator o Global Administrator del Banco de Occidente deberá realizar las siguientes configuraciones mediante PowerShell:

Primero, habilitar **Enterprise Voice** para cada usuario que recibirá llamadas del agente Optinoc. Segundo, habilitar **ACS Federation Access** a nivel global del tenant, lo cual permite que recursos de Azure Communication Services puedan comunicarse con usuarios de Teams. Tercero, agregar el Immutable Resource ID del recurso ACS a la lista de **Allowed ACS Resources** en la configuración de federación de Teams. Sin estas configuraciones, las llamadas del agente serán rechazadas con códigos de error de autorización. Estas configuraciones son persistentes y solo deben realizarse una vez durante el despliegue inicial.

---

## 5. Conectividad VPN con Sistemas de Monitoreo

Para que el agente Optinoc pueda consultar información de los sistemas de monitoreo del banco (Zabbix, Grafana, bases de datos IBM DB2, u otras fuentes de datos del NOC/SOC), se requiere establecer una **conexión VPN Site-to-Site** entre la máquina virtual donde reside Optinoc y la red interna donde se encuentran dichos sistemas. Esta conectividad permite que el agente, durante una llamada, pueda ejecutar consultas en tiempo real a las bases de datos del banco para informar al operador sobre el estado de tablespaces, alertas activas, métricas de rendimiento, o cualquier información que se configure en el sistema. Sin esta conectividad, el agente solo podría mantener conversaciones genéricas sin acceso a datos operativos del banco.

---

## 6. Dominio y Certificado SSL

El servicio Optinoc expone endpoints HTTP/HTTPS y WebSocket que deben ser accesibles desde internet para que Azure Communication Services pueda enviar los callbacks de eventos de llamada y establecer el streaming de audio. Por lo tanto, se requiere:

Un **subdominio dedicado** bajo el dominio del banco (por ejemplo: optinoc.bancooccidente.com o voicebot.bancooccidente.com) que apunte a la dirección IP pública de la máquina virtual o al servicio de exposición que se utilice (como Azure Application Gateway, Cloudflare Tunnel, o similar).

Un **certificado SSL/TLS válido** para dicho dominio, ya que Azure Communication Services requiere conexiones seguras (HTTPS y WSS) para los callbacks y el media streaming. El certificado puede ser emitido por una autoridad certificadora reconocida o generado mediante Let's Encrypt si las políticas del banco lo permiten.

---

## 7. Integración con Infraestructura Cisco (Opcional)

Si el Banco de Occidente desea que el agente Optinoc pueda realizar llamadas no solo a usuarios de Teams sino también a líneas telefónicas tradicionales (PSTN) o extensiones del sistema de telefonía existente, se requiere que el banco cuente con infraestructura de **Cisco CUBE (Unified Border Element)** o un SIP Trunk compatible. En este escenario, Azure Communication Services puede configurarse con Direct Routing para enrutar llamadas salientes a través del CUBE del banco hacia la red telefónica. Esta integración requiere coordinación entre el equipo de redes/telefonía del banco y el equipo de implementación de Optinoc para configurar correctamente los perfiles SIP, códecs de audio soportados y reglas de enrutamiento.

---

## 8. Accesos y Credenciales

Para la implementación y operación continua del sistema, se requieren los siguientes accesos:

- **Azure Portal**: Acceso con permisos de contribuidor al resource group donde se desplegará la infraestructura de Optinoc.
- **Microsoft Teams Admin Center**: Acceso temporal para realizar la configuración inicial de permisos y federación ACS.
- **Object IDs de usuarios de Teams**: Para cada usuario que recibirá llamadas, se requiere su Object ID de Azure Active Directory (GUID), no el correo electrónico.
- **Tenant ID de Microsoft 365**: El identificador único del tenant del banco, necesario para la configuración del sistema.
- **Credenciales de conexión a sistemas de monitoreo**: Si se desea integración con DB2, Zabbix u otros sistemas, se requieren las credenciales de acceso (solo lectura es suficiente) para que el agente pueda consultar información durante las llamadas.

---

## Resumen de Requerimientos

1. Licencias Teams Phone Standard (una por cada usuario receptor de llamadas)
2. Máquina Virtual Azure B2s (2 vCPUs, 4GB RAM, 64GB SSD) en el tenant del banco
3. Recurso Azure Communication Services en el tenant del banco
4. Configuración de permisos de Teams (Enterprise Voice, ACS Federation)
5. VPN Site-to-Site hacia sistemas de monitoreo internos
6. Dominio + Certificado SSL para exposición del servicio
7. (Opcional) Cisco CUBE para integración PSTN

---

## Contacto

**Optimize IT**
Implementación y soporte de Optinoc VoiceBot
