# Guia para Reunion: Conexion Cisco CUBE + Azure Communication Services (ACS)

> **Proposito:** Documento de referencia para reuniones con el cliente sobre la integracion de Direct Routing entre Azure Communication Services y Cisco CUBE.

---

## Tabla de Contenidos

1. [Por que se necesita esta arquitectura](#1-por-que-se-necesita-esta-arquitectura)
2. [Diagrama de conexion general](#2-diagrama-de-conexion-general)
3. [Glosario de terminos](#3-glosario-de-terminos)
4. [Arquitectura detallada con ubicacion de componentes](#4-arquitectura-detallada-con-ubicacion-de-componentes)
5. [Que debe configurar cada parte](#5-que-debe-configurar-cada-parte)
6. [Requisitos tecnicos del certificado TLS](#6-requisitos-tecnicos-del-certificado-tls)
7. [Reglas de firewall](#7-reglas-de-firewall)
8. [Dial-peers en el CUBE](#8-dial-peers-en-el-cube)
9. [Flujo de una llamada paso a paso](#9-flujo-de-una-llamada-paso-a-paso)
10. [Flujo de protocolos](#10-flujo-de-protocolos)
11. [Advertencia sobre certificacion](#11-advertencia-sobre-certificacion)
12. [Preguntas frecuentes del cliente](#12-preguntas-frecuentes-del-cliente)
13. [Checklist de implementacion](#13-checklist-de-implementacion)
14. [Referencias oficiales](#14-referencias-oficiales)

---

## 1. Por que se necesita esta arquitectura

**Problema:** Azure no vende numeros telefonicos en Colombia.

**Solucion:** Usar **Direct Routing** - conectar la infraestructura telefonica que ya tiene el cliente (Cisco CUBE) con Azure.

---

## 2. Diagrama de conexion general

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NUBE DE AZURE                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │         Azure Communication Services (ACS)                             │  │
│  │         (Servicio de Microsoft para llamadas en la nube)              │  │
│  │                                                                        │  │
│  │   - Aplicacion OPTI (bot de voz)                                      │  │
│  │   - Registra el SBC del cliente                                       │  │
│  │   - Configura voice routes (reglas de marcado)                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                               │
│                              │ Senalizacion SIP (cifrada con TLS)           │
│                              │ Puerto TCP 5061                               │
│                              │                                               │
│                              │ Audio (cifrado con SRTP)                     │
│                              │ Puertos UDP 49152-53247                       │
│                              ▼                                               │
│         IPs de salida: 52.112.0.0/14 y 52.120.0.0/14                        │
└─────────────────────────────────────────────────────────────────────────────┘
                               │
                               │ INTERNET PUBLICO
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RED DEL CLIENTE                                       │
│                                                                              │
│   ┌─────────────────┐                                                       │
│   │    FIREWALL     │  Debe permitir trafico DESDE las IPs de Microsoft    │
│   │    del cliente  │  hacia el CUBE                                        │
│   └────────┬────────┘                                                       │
│            │                                                                 │
│            ▼                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    CISCO CUBE                                        │   │
│   │   (Controlador de Borde de Sesion - convierte protocolos)           │   │
│   │                                                                      │   │
│   │   FQDN: sbc.bancooccidente.com  <── Debe ser PUBLICO (con DNS)     │   │
│   │   Puerto: 5061 (TCP)                                                 │   │
│   │                                                                      │   │
│   │   Componentes que DEBE tener configurados:                          │   │
│   │   ┌──────────────────────────────────────────────────────────────┐  │   │
│   │   │ TLS 1.2 + Certificado de CA Publica                          │  │   │
│   │   │ └─> Cifra la senalizacion (los comandos "llamar", "colgar")  │  │   │
│   │   ├──────────────────────────────────────────────────────────────┤  │   │
│   │   │ SRTP                                                          │  │   │
│   │   │ └─> Cifra el audio (la voz de la conversacion)               │  │   │
│   │   ├──────────────────────────────────────────────────────────────┤  │   │
│   │   │ Dial-peers                                                    │  │   │
│   │   │ └─> Reglas de enrutamiento hacia Microsoft                   │  │   │
│   │   └──────────────────────────────────────────────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│            │                                                                 │
│            ▼                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │           CUCM (Cisco Unified Communications Manager)                │   │
│   │           y red telefonica interna del cliente                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Glosario de terminos

| Abreviacion | Nombre Completo | Que es | Analogia simple |
|-------------|-----------------|--------|-----------------|
| **ACS** | Azure Communication Services | Servicio de Microsoft en la nube para manejar llamadas, SMS, video. Es donde corre nuestra aplicacion OPTI. | Como un "call center virtual" en la nube |
| **CUBE** | Cisco Unified Border Element | Equipo fisico o virtual de Cisco que actua como puerta de enlace entre redes telefonicas diferentes. Traduce protocolos. | Como un "traductor" entre idiomas telefonicos |
| **SBC** | Session Border Controller (Controlador de Borde de Sesion) | Dispositivo que controla las llamadas VoIP en el borde de una red. El CUBE es un tipo de SBC. | Como un "guardia fronterizo" para llamadas |
| **Direct Routing** | Enrutamiento Directo | Metodo para conectar tu propia infraestructura telefonica con servicios en la nube de Microsoft | Como un "puente privado" entre tu red y Azure |
| **FQDN** | Fully Qualified Domain Name (Nombre de Dominio Completo) | Nombre DNS completo del servidor, ej: `sbc.bancooccidente.com` | Como la "direccion postal" del CUBE en internet |
| **TLS** | Transport Layer Security (Seguridad de Capa de Transporte) | Protocolo de cifrado para la senalizacion SIP (los mensajes de control de llamada) | Como HTTPS pero para llamadas - protege los comandos |
| **SRTP** | Secure Real-time Transport Protocol (Protocolo de Transporte en Tiempo Real Seguro) | Protocolo de cifrado para el audio de la llamada | Protege que nadie escuche la conversacion |
| **SIP** | Session Initiation Protocol (Protocolo de Inicio de Sesion) | Protocolo estandar para establecer, modificar y terminar llamadas VoIP | El "lenguaje" que usan los equipos para coordinar llamadas |
| **Dial-peer** | Regla de marcado | Configuracion en el CUBE que define hacia donde enviar llamadas segun el destino | Como una "tabla de rutas" para llamadas |
| **PSTN** | Public Switched Telephone Network (Red Telefonica Publica Conmutada) | La red telefonica tradicional de lineas fijas y celulares | Los telefonos "normales" |
| **CUCM** | Cisco Unified Communications Manager | Sistema de telefonia IP de Cisco que administra telefonos internos | La "central telefonica" interna del cliente |
| **CA** | Certificate Authority (Autoridad Certificadora) | Empresa que emite certificados digitales de confianza (DigiCert, GlobalSign, etc.) | Como un "notario digital" que valida identidades |
| **RTP** | Real-time Transport Protocol (Protocolo de Transporte en Tiempo Real) | Protocolo para transmitir audio/video en tiempo real | El "transporte" del audio de voz |
| **VoIP** | Voice over IP (Voz sobre IP) | Tecnologia para transmitir voz a traves de redes de datos (internet) | Llamadas por internet en vez de linea telefonica |

---

## 4. Arquitectura detallada con ubicacion de componentes

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                         │
│                                    NUBE DE MICROSOFT AZURE                                              │
│                                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                                                 │   │
│   │                        ACS (Azure Communication Services)                                       │   │
│   │                    Servicio de comunicaciones en la nube de Microsoft                          │   │
│   │                                                                                                 │   │
│   │   ┌───────────────────────┐         ┌───────────────────────────────────────────────────────┐  │   │
│   │   │                       │         │                                                       │  │   │
│   │   │   APLICACION OPTI     │ <─────> │              CALL AUTOMATION                          │  │   │
│   │   │   (Bot de voz con IA) │         │         (Motor de llamadas de ACS)                    │  │   │
│   │   │                       │         │                                                       │  │   │
│   │   │   - FastAPI Server    │         │   Aqui se configura:                                  │  │   │
│   │   │   - OpenAI Realtime   │         │     - SBC registrado (FQDN + puerto del cliente)     │  │   │
│   │   │   - WebSocket bidi    │         │     - Voice Routes (reglas de marcado +57...)        │  │   │
│   │   │                       │         │                                                       │  │   │
│   │   └───────────────────────┘         └───────────────────────────────────────────────────────┘  │   │
│   │                                                          │                                      │   │
│   └──────────────────────────────────────────────────────────┼──────────────────────────────────────┘   │
│                                                              │                                          │
│   ┌──────────────────────────────────────────────────────────┼──────────────────────────────────────┐   │
│   │                                                          │                                      │   │
│   │                    PSTN HUB de Microsoft                 │                                      │   │
│   │              (Puerta de enlace SIP de Azure)             │                                      │   │
│   │                                                          ▼                                      │   │
│   │   ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │   │
│   │   │                                                                                         │  │   │
│   │   │    sip.pstnhub.microsoft.com      ──>  Primario                                        │  │   │
│   │   │    sip2.pstnhub.microsoft.com     ──>  Failover 1                                      │  │   │
│   │   │    sip3.pstnhub.microsoft.com     ──>  Failover 2                                      │  │   │
│   │   │                                                                                         │  │   │
│   │   │    IPs de salida: 52.112.0.0/14  y  52.120.0.0/14                                      │  │   │
│   │   │                                                                                         │  │   │
│   │   └─────────────────────────────────────────────────────────────────────────────────────────┘  │   │
│   │                                                          │                                      │   │
│   └──────────────────────────────────────────────────────────┼──────────────────────────────────────┘   │
│                                                              │                                          │
└──────────────────────────────────────────────────────────────┼──────────────────────────────────────────┘
                                                               │
                                                               │
                     ══════════════════════════════════════════╪══════════════════════════════════════════
                                                               │
                                         I N T E R N E T      │      P U B L I C O
                                                               │
                     ══════════════════════════════════════════╪══════════════════════════════════════════
                                                               │
                                                               │
                     ┌─────────────────────────────────────────┴─────────────────────────────────────────┐
                     │                                                                                   │
                     │   ┌───────────────────────────────────────────────────────────────────────────┐   │
                     │   │                                                                           │   │
                     │   │   CANAL DE SENALIZACION                    CANAL DE MEDIA (AUDIO)        │   │
                     │   │                                                                           │   │
                     │   │   ┌─────────────────────────────┐         ┌─────────────────────────┐     │   │
                     │   │   │                             │         │                         │     │   │
                     │   │   │   SIP sobre TLS             │         │   RTP sobre SRTP        │     │   │
                     │   │   │   (SIP = Session Initiation │         │   (RTP = Real-time      │     │   │
                     │   │   │    Protocol - Protocolo de  │         │    Transport Protocol   │     │   │
                     │   │   │    inicio de sesion)        │         │    Protocolo de         │     │   │
                     │   │   │                             │         │    transporte en        │     │   │
                     │   │   │   TLS 1.2                   │         │    tiempo real)         │     │   │
                     │   │   │   (Transport Layer Security │         │                         │     │   │
                     │   │   │    Seguridad de capa de     │         │   SRTP                  │     │   │
                     │   │   │    transporte)              │         │   (Secure RTP - RTP     │     │   │
                     │   │   │                             │         │    Seguro)              │     │   │
                     │   │   │   ┌───────────────────┐     │         │                         │     │   │
                     │   │   │   │ Puerto TCP 5061   │     │         │   ┌─────────────────┐   │     │   │
                     │   │   │   └───────────────────┘     │         │   │ Puertos UDP     │   │     │   │
                     │   │   │                             │         │   │ 49152 - 53247   │   │     │   │
                     │   │   │   Mensajes:                 │         │   └─────────────────┘   │     │   │
                     │   │   │   - INVITE (iniciar)        │         │                         │     │   │
                     │   │   │   - BYE (colgar)            │         │   Contenido:            │     │   │
                     │   │   │   - ACK (confirmar)         │         │   - Audio de voz        │     │   │
                     │   │   │   - CANCEL (cancelar)       │         │   - Bidireccional       │     │   │
                     │   │   │                             │         │                         │     │   │
                     │   │   └─────────────────────────────┘         └─────────────────────────┘     │   │
                     │   │                                                                           │   │
                     │   └───────────────────────────────────────────────────────────────────────────┘   │
                     │                                         │                                         │
                     └─────────────────────────────────────────┼─────────────────────────────────────────┘
                                                               │
                                                               │
                                                               ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                          │
│                                    RED DEL CLIENTE (Banco de Occidente)                                  │
│                                                                                                          │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                                                  │   │
│   │                                         FIREWALL                                                 │   │
│   │                                                                                                  │   │
│   │   Reglas requeridas (ENTRANTE):                                                                  │   │
│   │   ┌────────────────────────────────────────────────────────────────────────────────────────┐     │   │
│   │   │  PERMITIR TCP 5061        DESDE 52.112.0.0/14, 52.120.0.0/14  ->  Hacia IP del CUBE   │     │   │
│   │   │  PERMITIR UDP 49152-53247 DESDE 52.112.0.0/14, 52.120.0.0/14  ->  Hacia IP del CUBE   │     │   │
│   │   └────────────────────────────────────────────────────────────────────────────────────────┘     │   │
│   │                                                                                                  │   │
│   └──────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                    │                                                     │
│                                                    ▼                                                     │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                                                  │   │
│   │      SBC (Session Border Controller) = CISCO CUBE (Cisco Unified Border Element)                │   │
│   │      ════════════════════════════════════════════════════════════════════════════               │   │
│   │                                                                                                  │   │
│   │      El CUBE es el "traductor" entre la red de Microsoft y la red telefonica del cliente        │   │
│   │                                                                                                  │   │
│   │   ┌────────────────────────────────────────────────────────────────────────────────────────┐     │   │
│   │   │                                                                                        │     │   │
│   │   │   FQDN PUBLICO: sbc.bancooccidente.com                                                │     │   │
│   │   │   (Fully Qualified Domain Name - Nombre de dominio completamente calificado)          │     │   │
│   │   │                                                                                        │     │   │
│   │   │   ┌─────────────────┐     Debe tener registro DNS tipo A:                             │     │   │
│   │   │   │  DNS Publico    │     sbc.bancooccidente.com  ->  200.X.X.X (IP publica del CUBE)│     │   │
│   │   │   └─────────────────┘                                                                  │     │   │
│   │   │                                                                                        │     │   │
│   │   └────────────────────────────────────────────────────────────────────────────────────────┘     │   │
│   │                                                                                                  │   │
│   │   ┌────────────────────────────────────────────────────────────────────────────────────────┐     │   │
│   │   │                                                                                        │     │   │
│   │   │   CERTIFICADO TLS (instalado en el CUBE)                                              │     │   │
│   │   │   ─────────────────────────────────────────                                           │     │   │
│   │   │                                                                                        │     │   │
│   │   │   - Emisor: CA publica (DigiCert, GlobalSign, Sectigo, etc.)                          │     │   │
│   │   │             NO autofirmado / NO CA corporativa                                         │     │   │
│   │   │                                                                                        │     │   │
│   │   │   - CN/SAN: Debe coincidir con el FQDN (sbc.bancooccidente.com)                       │     │   │
│   │   │                                                                                        │     │   │
│   │   │   - Key size: Minimo 2048 bits                                                        │     │   │
│   │   │                                                                                        │     │   │
│   │   │   - Cipher suites soportados:                                                         │     │   │
│   │   │     - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384                                           │     │   │
│   │   │     - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256                                           │     │   │
│   │   │                                                                                        │     │   │
│   │   └────────────────────────────────────────────────────────────────────────────────────────┘     │   │
│   │                                                                                                  │   │
│   │   ┌────────────────────────────────────────────────────────────────────────────────────────┐     │   │
│   │   │                                                                                        │     │   │
│   │   │   CONFIGURACION SRTP (en el CUBE)                                                     │     │   │
│   │   │   ───────────────────────────────                                                     │     │   │
│   │   │                                                                                        │     │   │
│   │   │   Cifrado obligatorio: AES_CM_128_HMAC_SHA1_80                                        │     │   │
│   │   │                                                                                        │     │   │
│   │   │   Codecs soportados: G.711 u-law, G.711 A-law, G.722, SILK, G.729                    │     │   │
│   │   │                                                                                        │     │   │
│   │   └────────────────────────────────────────────────────────────────────────────────────────┘     │   │
│   │                                                                                                  │   │
│   │   ┌────────────────────────────────────────────────────────────────────────────────────────┐     │   │
│   │   │                                                                                        │     │   │
│   │   │   DIAL-PEERS (reglas de enrutamiento configuradas en el CUBE)                         │     │   │
│   │   │   ───────────────────────────────────────────────────────────                         │     │   │
│   │   │                                                                                        │     │   │
│   │   │   ┌─────────────────────────────────────────────────────────────────────────────┐     │     │   │
│   │   │   │  Dial-peer ENTRANTE (llamadas que vienen de Microsoft):                     │     │     │   │
│   │   │   │                                                                             │     │     │   │
│   │   │   │    Origen: sip.pstnhub.microsoft.com                                        │     │     │   │
│   │   │   │    Accion: Enviar a la red PSTN interna / CUCM                              │     │     │   │
│   │   │   │                                                                             │     │     │   │
│   │   │   └─────────────────────────────────────────────────────────────────────────────┘     │     │   │
│   │   │                                                                                        │     │   │
│   │   │   ┌─────────────────────────────────────────────────────────────────────────────┐     │     │   │
│   │   │   │  Dial-peer SALIENTE (llamadas que van hacia Microsoft):                     │     │     │   │
│   │   │   │                                                                             │     │     │   │
│   │   │   │    Destino 1: sip.pstnhub.microsoft.com:5061    (primario)                  │     │     │   │
│   │   │   │    Destino 2: sip2.pstnhub.microsoft.com:5061   (failover)                  │     │     │   │
│   │   │   │    Destino 3: sip3.pstnhub.microsoft.com:5061   (failover)                  │     │     │   │
│   │   │   │                                                                             │     │     │   │
│   │   │   └─────────────────────────────────────────────────────────────────────────────┘     │     │   │
│   │   │                                                                                        │     │   │
│   │   └────────────────────────────────────────────────────────────────────────────────────────┘     │   │
│   │                                                                                                  │   │
│   │   Version requerida: IOS XE 16.11 o superior (para TLS 1.2 completo)                            │   │
│   │                                                                                                  │   │
│   └──────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                    │                                                     │
│                                                    ▼                                                     │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                                                  │   │
│   │                    CUCM (Cisco Unified Communications Manager)                                   │   │
│   │                    ═══════════════════════════════════════════                                   │   │
│   │                                                                                                  │   │
│   │                    Central telefonica interna que administra:                                    │   │
│   │                    - Telefonos IP de escritorio                                                  │   │
│   │                    - Softphones                                                                  │   │
│   │                    - Troncales hacia la PSTN                                                     │   │
│   │                                                                                                  │   │
│   └──────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                    │                                                     │
│                                                    ▼                                                     │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                                                  │   │
│   │                              PSTN (Red Telefonica Publica)                                       │   │
│   │                              ═════════════════════════════                                       │   │
│   │                                                                                                  │   │
│   │                    Conexion a lineas telefonicas tradicionales                                   │   │
│   │                    (celulares, fijos, etc.)                                                      │   │
│   │                                                                                                  │   │
│   │                              Telefono del tecnico destino                                        │   │
│   │                                                                                                  │   │
│   └──────────────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Que debe configurar cada parte

### 5.1 El Cliente debe proveer/configurar

| Componente | Donde se configura | Ejemplo | Quien lo hace |
|------------|-------------------|---------|---------------|
| **FQDN publico** | DNS del cliente | `sbc.bancooccidente.com` -> IP publica del CUBE | Equipo de redes |
| **Puerto SIP** | CUBE | `5061` (TCP con TLS) | Equipo de telefonia |
| **Numero telefonico** | Asignacion interna | `+576012345678` (para caller ID) | Equipo de telefonia |
| **Certificado TLS** | CUBE | De CA publica (DigiCert, GlobalSign, Sectigo) | Equipo de redes/seguridad |
| **TLS 1.2** | CUBE | Habilitar version 1.2 | Equipo de telefonia |
| **SRTP** | CUBE | Cifrado `AES_CM_128_HMAC_SHA1_80` | Equipo de telefonia |
| **Dial-peers** | CUBE | Reglas hacia `sip.pstnhub.microsoft.com` | Equipo de telefonia |
| **Firewall** | Firewall perimetral | Abrir IPs de Microsoft | Equipo de seguridad |

### 5.2 Optinoc debe configurar

| Componente | Donde se configura | Que se pone |
|------------|-------------------|-------------|
| **Registrar el SBC** | Azure Portal -> ACS | FQDN y puerto que provea el cliente |
| **Voice Routes** | Azure Portal -> ACS | Patron `^\+57(\d+)$` para Colombia |
| **Variable de entorno** | Aplicacion OPTI | `ACS_PHONE_NUMBER=+576012345678` |
| **Codigo** | `main.py` | `source_caller_id_number` en llamadas |

### 5.3 Resumen visual

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│                           RESUMEN: QUE CONFIGURA CADA QUIEN                             │
│                                                                                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                         OPTINOC CONFIGURA EN AZURE                              │   │
│   │                                                                                 │   │
│   │    ACS Portal:                                                                  │   │
│   │    |── Registrar el SBC (con el FQDN y puerto que de el cliente)               │   │
│   │    └── Voice Routes (patron ^\+57(\d+)$ para numeros de Colombia)              │   │
│   │                                                                                 │   │
│   │    Aplicacion:                                                                  │   │
│   │    └── Variable ACS_PHONE_NUMBER con el numero que de el cliente               │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                     EL CLIENTE CONFIGURA EN SU RED                              │   │
│   │                                                                                 │   │
│   │    DNS:                                                                         │   │
│   │    └── Registro A: sbc.dominio.com -> IP publica del CUBE                      │   │
│   │                                                                                 │   │
│   │    Firewall:                                                                    │   │
│   │    |── TCP 5061 desde 52.112.0.0/14, 52.120.0.0/14                             │   │
│   │    └── UDP 49152-53247 desde 52.112.0.0/14, 52.120.0.0/14                      │   │
│   │                                                                                 │   │
│   │    CUBE:                                                                        │   │
│   │    |── Certificado TLS de CA publica                                           │   │
│   │    |── TLS 1.2 habilitado                                                      │   │
│   │    |── SRTP con cifrado AES_CM_128_HMAC_SHA1_80                                │   │
│   │    └── Dial-peers hacia sip.pstnhub.microsoft.com                              │   │
│   │                                                                                 │   │
│   │    El cliente nos provee:                                                       │   │
│   │    |── FQDN del CUBE (ej: sbc.bancooccidente.com)                              │   │
│   │    |── Puerto SIP (generalmente 5061)                                          │   │
│   │    └── Numero telefonico para caller ID (ej: +576012345678)                    │   │
│   │                                                                                 │   │
│   └─────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Requisitos tecnicos del certificado TLS

```
┌────────────────────────────────────────────────────────────────────┐
│                    REQUISITOS DEL CERTIFICADO                       │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Emisor:      CA publica (DigiCert, GlobalSign, Sectigo, etc.)     │
│               [X] NO autofirmado                                    │
│               [X] NO CA interna/corporativa                         │
│                                                                     │
│  CN o SAN:    Debe incluir el FQDN del CUBE                        │
│               Ejemplo: sbc.bancooccidente.com                       │
│                                                                     │
│  Key size:    Minimo 2048 bits                                     │
│                                                                     │
│  EKU:         Server Authentication                                 │
│               (Extended Key Usage - Autenticacion de Servidor)      │
│                                                                     │
│  Razon:       Microsoft solo acepta certificados de CAs que        │
│               esten en el Microsoft Trusted Root Certificate        │
│               Program                                               │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### Cipher suites soportados

- `TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384`
- `TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`
- `TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA384`
- `TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256`

---

## 7. Reglas de firewall

```
┌────────────────────────────────────────────────────────────────────┐
│                    REGLAS DE FIREWALL REQUERIDAS                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PERMITIR conexiones ENTRANTES desde:                              │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Origen (IPs de Microsoft Azure):                           │   │
│  │    - 52.112.0.0/14  (rango: 52.112.0.0 - 52.115.255.255)   │   │
│  │    - 52.120.0.0/14  (rango: 52.120.0.0 - 52.123.255.255)   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Destino: IP del CUBE                                       │   │
│  │                                                              │   │
│  │  Puertos:                                                    │   │
│  │    - TCP 5061        -> Senalizacion SIP (con TLS)          │   │
│  │    - UDP 49152-53247 -> Media/Audio (RTP/SRTP)              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### Regla resumida para copiar

```
PERMITIR TCP 5061       DESDE 52.112.0.0/14, 52.120.0.0/14 HACIA [IP_DEL_CUBE]
PERMITIR UDP 49152-53247 DESDE 52.112.0.0/14, 52.120.0.0/14 HACIA [IP_DEL_CUBE]
```

---

## 8. Dial-peers en el CUBE

Los dial-peers son las reglas que le dicen al CUBE hacia donde enviar las llamadas.

```
┌────────────────────────────────────────────────────────────────────┐
│              DIAL-PEERS HACIA MICROSOFT (en el CUBE)               │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Destinos de Microsoft (en orden de prioridad):                    │
│                                                                     │
│    1. sip.pstnhub.microsoft.com:5061   <- Primario                 │
│    2. sip2.pstnhub.microsoft.com:5061  <- Failover 1               │
│    3. sip3.pstnhub.microsoft.com:5061  <- Failover 2               │
│                                                                     │
│  Ejemplo conceptual de la configuracion:                           │
│                                                                     │
│    Dial-peer 100 (entrante):                                       │
│      "Si llega llamada DESDE Microsoft -> enviar a red interna"   │
│                                                                     │
│    Dial-peer 200 (saliente):                                       │
│      "Si hay llamada HACIA Microsoft -> enviar por TLS:5061"      │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## 9. Flujo de una llamada paso a paso

```
PASO 1: La aplicacion OPTI inicia una llamada
        └─> POST /calls/outbound con target_number: "+573001234567"

PASO 2: ACS busca como llegar a ese numero
        └─> Voice route dice: "+57... va por el SBC del cliente"

PASO 3: ACS se conecta al CUBE del cliente
        └─> SIP INVITE via TLS al FQDN del CUBE (puerto 5061)
        └─> Desde IPs: 52.112.x.x o 52.120.x.x

PASO 4: El CUBE recibe la llamada y la enruta
        └─> Dial-peer dice: "Esta llamada va a la red PSTN"
        └─> El CUBE conecta a traves de la infraestructura Cisco/CUCM

PASO 5: El telefono destino suena y la persona contesta
        └─> Evento "CallConnected" llega a OPTI

PASO 6: Comienza la conversacion bidireccional
        └─> Audio cifrado con SRTP fluye en ambas direcciones
        └─> OPTI (el bot de IA) comienza a hablar
```

---

## 10. Flujo de protocolos

```
┌──────────────┐                                              ┌──────────────┐
│              │           SENALIZACION (SIP/TLS)             │              │
│    AZURE     │  ─────────────────────────────────────────>  │    CUBE      │
│    ACS       │         TCP 5061 - Comandos cifrados         │   (SBC)      │
│              │         "INVITE", "BYE", "ACK"               │              │
│              │                                              │              │
│              │              MEDIA (RTP/SRTP)                │              │
│              │  <═══════════════════════════════════════>   │              │
│              │       UDP 49152-53247 - Audio cifrado        │              │
│              │            Voz bidireccional                 │              │
└──────────────┘                                              └──────────────┘

Leyenda:
  ─────>  Senalizacion unidireccional por mensaje (request/response)
  <═══>   Media bidireccional continuo (audio en ambos sentidos)
```

---

## 11. Advertencia sobre certificacion

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PUNTO CRITICO PARA EL CLIENTE                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Cisco CUBE NO esta oficialmente certificado para ACS               │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  SBCs Certificados para ACS:                               │     │
│  │    [OK] AudioCodes                                         │     │
│  │    [OK] Ribbon                                             │     │
│  │    [OK] Oracle                                             │     │
│  │    [OK] Metaswitch                                         │     │
│  │    [OK] TE-SYSTEMS                                         │     │
│  │    [X]  Cisco CUBE (NO certificado)                        │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  Implicaciones:                                                      │
│    - PUEDE funcionar porque ACS comparte backend con Teams          │
│      Direct Routing (donde Cisco SI esta certificado)               │
│    - Microsoft NO da soporte oficial si hay problemas               │
│    - Se recomienda hacer prueba de concepto antes de produccion     │
│                                                                      │
│  Contacto para informacion de certificacion:                        │
│    acsdrcertification@microsoft.com                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 12. Preguntas frecuentes del cliente

| Pregunta | Respuesta |
|----------|-----------|
| **"Por que no compran ustedes un numero?"** | Azure no vende numeros telefonicos para Colombia. Direct Routing usando la infraestructura existente es la unica opcion. |
| **"Que certificado necesitamos?"** | Uno de CA publica (DigiCert, GlobalSign, Sectigo, Let's Encrypt). NO autofirmado, NO CA corporativa interna. |
| **"Por que el FQDN debe ser publico?"** | Porque ACS esta en la nube de Microsoft, no en su red. Azure necesita resolver el DNS y conectarse a traves de internet. |
| **"Cuanto tarda en activarse?"** | Despues de registrar el SBC en ACS, aproximadamente 15 minutos para que el estado cambie a "Online". |
| **"Que pasa si el CUBE esta en mantenimiento?"** | Las llamadas fallan. Se puede configurar un SBC secundario como failover. |
| **"Que version de IOS necesita el CUBE?"** | IOS XE 16.11 o superior para soporte completo de TLS 1.2. |
| **"Quien da soporte si algo falla?"** | Optinoc para la aplicacion, ustedes para el CUBE. Nota: Microsoft no da soporte oficial para CUBE con ACS. |
| **"Cuanto cuesta?"** | ACS cobra ~$0.004 USD/minuto. El costo PSTN depende de su proveedor actual. |
| **"Pueden grabar las llamadas?"** | Si, ACS soporta grabacion (+$0.002/min). |
| **"Funciona con nuestro Call Manager (CUCM)?"** | Si. El CUBE se conecta al Call Manager, ACS se conecta al CUBE. No hay cambio en la arquitectura interna. |
| **"Cuantas llamadas simultaneas soporta?"** | Depende de la capacidad del CUBE y el ancho de banda. ACS no tiene limite practico. |
| **"Pueden usar nuestro certificado interno/corporativo?"** | No. Microsoft solo acepta certificados de CAs que esten en el Microsoft Trusted Root Certificate Program. |

---

## 13. Checklist de implementacion

### El cliente debe completar:

- [ ] Proveer FQDN del CUBE
- [ ] Proveer puerto SIP (generalmente 5061)
- [ ] Proveer numero telefonico para caller ID
- [ ] Instalar certificado TLS de CA publica en CUBE
- [ ] Configurar TLS 1.2 en CUBE
- [ ] Configurar SRTP en CUBE
- [ ] Abrir firewall para IPs de Microsoft (52.112.0.0/14, 52.120.0.0/14)
- [ ] Configurar dial-peers hacia Microsoft en CUBE

### Optinoc debe completar:

- [ ] Registrar SBC en Azure Communication Services
- [ ] Configurar voice routes en ACS
- [ ] Verificar estado "Online" del SBC
- [ ] Configurar variable ACS_PHONE_NUMBER en .env
- [ ] Modificar codigo para incluir source_caller_id_number
- [ ] Probar llamada de prueba

---

## 14. Referencias oficiales

| Documento | URL |
|-----------|-----|
| Requisitos de Infraestructura | https://learn.microsoft.com/en-us/azure/communication-services/concepts/telephony/direct-routing-infrastructure |
| SBCs Certificados | https://learn.microsoft.com/en-us/azure/communication-services/concepts/telephony/certified-session-border-controllers |
| Provisioning Direct Routing | https://learn.microsoft.com/en-us/azure/communication-services/concepts/telephony/direct-routing-provisioning |
| IPs de Azure (JSON actualizado) | https://www.microsoft.com/en-us/download/details.aspx?id=56519 |

---

## Notas adicionales

### Sobre TLS (Transport Layer Security)

**Que es:** Cifrado para la senalizacion SIP.

**Analogia:** Es como HTTPS pero para llamadas. Protege los mensajes de "llamar", "colgar", "transferir", etc.

```
Sin TLS:  CUBE ──── SIP en texto plano ────> Microsoft  [RECHAZADO]
Con TLS:  CUBE ──── SIP cifrado (TLS) ─────> Microsoft  [ACEPTADO]
```

### Sobre SRTP (Secure Real-time Transport Protocol)

**Que es:** Cifrado para el audio de la llamada.

**Analogia:** TLS protege los comandos, SRTP protege la voz.

```
Sin SRTP:  Audio en claro ──────> Cualquiera puede escuchar  [NO SEGURO]
Con SRTP:  Audio cifrado ───────> Solo los participantes     [SEGURO]
```

### Sobre Dial-peers

**Que es:** Reglas de enrutamiento de llamadas en el CUBE.

**Analogia:** Es como una tabla de rutas. "Si el destino es X, envia la llamada por Y".

---

*Documento generado para reunion con cliente - Proyecto Optinoc BOCC Realtime*
