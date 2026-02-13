# Requerimientos Tecnicos - Integracion OPTI con Banco de Occidente

**Proyecto:** Sistema de Llamadas Automatizadas con IA (OPTI)
**Cliente:** Banco de Occidente
**Fecha:** Febrero 2026
**Version:** 1.0
**Tipo de Documento:** Tecnico

---

## Tabla de Contenidos

1. [Resumen de la Solucion](#1-resumen-de-la-solucion)
2. [Arquitectura General](#2-arquitectura-general)
3. [Requerimientos Microsoft Teams y Azure](#3-requerimientos-microsoft-teams-y-azure)
4. [Requerimientos Central Telefonica (Cisco)](#4-requerimientos-central-telefonica-cisco)
5. [Requerimientos de Red y Seguridad](#5-requerimientos-de-red-y-seguridad)
6. [Accesos Requeridos](#6-accesos-requeridos)
7. [Matriz de Responsabilidades](#7-matriz-de-responsabilidades)
8. [Anexos Tecnicos](#8-anexos-tecnicos)

---

## 1. Resumen de la Solucion

### 1.1 Descripcion

OPTI es un asistente de voz con Inteligencia Artificial que realiza llamadas automatizadas para monitoreo NOC/SOC. El sistema utiliza Azure Communication Services como plataforma de comunicaciones y Azure OpenAI Realtime API para la conversacion inteligente.

### 1.2 Flujo de Llamadas

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FLUJO DE LLAMADAS OPTI                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                              ┌─────────────────┐                                │
│                              │      OPTI       │                                │
│                              │  (Azure + IA)   │                                │
│                              └────────┬────────┘                                │
│                                       │                                          │
│                                       ▼                                          │
│                              ┌─────────────────┐                                │
│                              │ Azure Comm.     │                                │
│                              │ Services (ACS)  │                                │
│                              └────────┬────────┘                                │
│                                       │                                          │
│                    ┌──────────────────┴──────────────────┐                      │
│                    │           Direct Routing            │                      │
│                    │         (SIP TLS + SRTP)            │                      │
│                    └──────────────────┬──────────────────┘                      │
│                                       │                                          │
│              ┌────────────────────────┼────────────────────────┐                │
│              │                        │                        │                │
│              ▼                        ▼                        ▼                │
│     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐        │
│     │ Microsoft Teams │     │   Cisco CUBE    │     │   Cisco CUBE    │        │
│     │   (50 usuarios) │     │  (via CUCM)     │     │  (via CUCM)     │        │
│     │                 │     │                 │     │                 │        │
│     │  Usuarios NOC   │     │   Telefonos     │     │   Celulares     │        │
│     │  en horario     │     │   Fijos         │     │   PSTN          │        │
│     └─────────────────┘     └─────────────────┘     └─────────────────┘        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Componentes Principales

| Componente | Descripcion | Responsable |
|------------|-------------|-------------|
| Azure Communication Services | Plataforma de llamadas y Direct Routing | Optinoc |
| Azure OpenAI Realtime | Motor de IA conversacional | Optinoc |
| Microsoft Teams | Cliente de comunicaciones para usuarios | Banco |
| Cisco CUBE | Session Border Controller para PSTN | Banco |
| Cisco CUCM | Central telefonica IP | Proveedor Telefonia |

---

## 2. Arquitectura General

### 2.1 Diagrama de Arquitectura

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                    AZURE CLOUD                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                                  │ │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────────┐  │ │
│  │  │  Azure OpenAI   │◄──►│   OPTI Server   │◄──►│  Azure Communication        │  │ │
│  │  │  Realtime API   │    │   (FastAPI)     │    │  Services (ACS)             │  │ │
│  │  │                 │    │                 │    │                             │  │ │
│  │  │  - GPT-4o-mini  │    │  - WebSocket    │    │  - Call Automation          │  │ │
│  │  │  - Audio I/O    │    │  - Media Stream │    │  - Direct Routing           │  │ │
│  │  │                 │    │  - Function     │    │  - Media Streaming          │  │ │
│  │  │                 │    │    Calling      │    │                             │  │ │
│  │  └─────────────────┘    └─────────────────┘    └──────────────┬──────────────┘  │ │
│  │                                                                │                 │ │
│  └────────────────────────────────────────────────────────────────┼─────────────────┘ │
│                                                                   │                   │
└───────────────────────────────────────────────────────────────────┼───────────────────┘
                                                                    │
                                           SIP TLS (5061) + SRTP    │
                                                                    │
┌───────────────────────────────────────────────────────────────────┼───────────────────┐
│                           INTERNET / MPLS                         │                   │
└───────────────────────────────────────────────────────────────────┼───────────────────┘
                                                                    │
                 ┌──────────────────────────────────────────────────┴───────┐
                 │                                                          │
                 ▼                                                          ▼
┌────────────────────────────────────┐              ┌────────────────────────────────────┐
│      INFRAESTRUCTURA BANCO         │              │       MICROSOFT 365 CLOUD          │
│                                    │              │                                    │
│  ┌──────────────────────────────┐  │              │  ┌──────────────────────────────┐  │
│  │       Cisco CUBE             │  │              │  │      Microsoft Teams         │  │
│  │    IOS XE 16.09.01           │  │              │  │                              │  │
│  │                              │  │              │  │    50 usuarios con           │  │
│  │  - SIP TLS (5061)            │  │              │  │    Teams Phone License       │  │
│  │  - SRTP                      │  │              │  │                              │  │
│  │  - Direct Routing            │  │              │  └──────────────────────────────┘  │
│  └──────────────┬───────────────┘  │              │                                    │
│                 │                  │              └────────────────────────────────────┘
│                 ▼                  │
│  ┌──────────────────────────────┐  │
│  │      Cisco CUCM              │  │
│  │   (Proveedor Telefonia)      │  │
│  │                              │  │
│  │  - Extensiones internas      │  │
│  │  - Troncales PSTN            │  │
│  └──────────────┬───────────────┘  │
│                 │                  │
│                 ▼                  │
│  ┌──────────────────────────────┐  │
│  │         PSTN                 │  │
│  │   Telefonos fijos/moviles   │  │
│  └──────────────────────────────┘  │
│                                    │
└────────────────────────────────────┘
```

### 2.2 Protocolos y Puertos

| Conexion | Protocolo | Puerto | Direccion |
|----------|-----------|--------|-----------|
| ACS ↔ CUBE | SIP sobre TLS | 5061 TCP | Bidireccional |
| ACS ↔ CUBE | SRTP (audio) | 1024-65535 UDP | Bidireccional |
| ACS ↔ Teams | Interno Microsoft | N/A | Interno |
| CUBE ↔ CUCM | SIP | 5060 | Interno |

---

## 3. Requerimientos Microsoft Teams y Azure

### 3.1 Licenciamiento Microsoft Teams

#### 3.1.1 Licencias Requeridas por Usuario (50 usuarios)

| Licencia | Cantidad | Descripcion |
|----------|----------|-------------|
| Microsoft 365 E3/E5 o Business | 50 | Licencia base (si no la tienen) |
| **Teams Phone Standard** | 50 | Habilita llamadas PSTN en Teams |

> **Nota:** Teams Phone Standard (anteriormente Phone System) es el add-on requerido para que los usuarios puedan recibir llamadas PSTN/Direct Routing.

#### 3.1.2 Verificacion de Licencias

El banco debe verificar que los 50 usuarios tengan asignada la licencia Teams Phone. Esto se puede validar en:
- Microsoft 365 Admin Center → Usuarios → Licencias
- O via PowerShell:
  ```powershell
  Get-MsolUser -UserPrincipalName usuario@banco.com | Select-Object Licenses
  ```

### 3.2 Azure Communication Services (ACS)

#### 3.2.1 Recurso ACS Requerido

Se debe crear un recurso de Azure Communication Services en el tenant de Azure del banco:

| Configuracion | Valor |
|---------------|-------|
| Nombre del recurso | `acs-opti-bocc` (sugerido) |
| Region | East US o East US 2 (recomendado) |
| Tipo de recurso | Azure Communication Services |

#### 3.2.2 Configuracion Direct Routing en ACS

**Paso 1: Registrar el SBC (Cisco CUBE)**

Via Azure CLI:
```bash
az communication phonenumbers direct-routing sbc create \
  --resource-group <RESOURCE_GROUP> \
  --name <ACS_RESOURCE_NAME> \
  --fqdn sbc.bancooccidente.com.co \
  --sip-signaling-port 5061
```

Via Azure Portal:
1. Ir al recurso ACS → Direct Routing → Session Border Controllers
2. Agregar SBC con FQDN y puerto 5061

**Paso 2: Configurar Voice Routes**

```bash
az communication phonenumbers direct-routing voice-route create \
  --resource-group <RESOURCE_GROUP> \
  --name <ACS_RESOURCE_NAME> \
  --route-name "Colombia-Route" \
  --number-pattern "^\+57(\d+)$" \
  --sbc-fqdn sbc.bancooccidente.com.co \
  --priority 1
```

#### 3.2.3 Acceso Requerido a ACS

| Acceso | Descripcion | Para que se necesita |
|--------|-------------|---------------------|
| Connection String | Cadena de conexion del recurso ACS | Autenticacion de la aplicacion OPTI |
| Managed Identity | Identidad administrada (opcional) | Autenticacion sin secretos |
| Contributor Role | Rol en el recurso ACS | Configurar Direct Routing |

### 3.3 Azure OpenAI

#### 3.3.1 Recurso Azure OpenAI Requerido

| Configuracion | Valor |
|---------------|-------|
| Nombre del recurso | `aoai-opti-bocc` (sugerido) |
| Region | East US 2 o Sweden Central |
| Modelo requerido | `gpt-4o-realtime-preview` |
| Tipo de despliegue | Standard |

#### 3.3.2 Acceso Requerido

| Acceso | Descripcion |
|--------|-------------|
| API Key | Clave de API del recurso |
| Endpoint | URL del recurso Azure OpenAI |
| Deployment Name | Nombre del despliegue del modelo |

> **Nota:** Azure OpenAI Realtime API requiere aprobacion de Microsoft. El banco debe solicitar acceso en: https://aka.ms/oai/access

### 3.4 Numeros Telefonicos

#### 3.4.1 Numero para Direct Routing

El banco debe proporcionar un numero telefonico (DID) que sera usado como caller ID para las llamadas de OPTI.

| Requisito | Descripcion |
|-----------|-------------|
| Formato | E.164 (ejemplo: +5712345678) |
| Tipo | DID del banco, enrutado via CUCM/CUBE |
| Configuracion | Debe estar configurado en CUCM para salir via CUBE hacia ACS |

---

## 4. Requerimientos Central Telefonica (Cisco)

### 4.1 Cisco CUBE - Session Border Controller

#### 4.1.1 Version de Software

| Componente | Version Actual | Compatibilidad |
|------------|----------------|----------------|
| Cisco CUBE | IOS XE 16.09.01 | Compatible con Direct Routing |
| ASR Platform | ASR1000 Series | Certificado por Microsoft |

> **Importante:** IOS XE 16.09.01 es compatible, pero se recomienda verificar que tenga los parches de seguridad mas recientes.

#### 4.1.2 Configuracion TLS/SRTP

**Cipher Suites Requeridos (CRITICO)**

Azure Communication Services requiere cipher suites especificos. La configuracion debe ser exacta:

```
! Configuracion de Cipher Suites para Microsoft ACS
voice class tls-cipher 1
 cipher 1 ECDHE-RSA-AES256-GCM-SHA384
 cipher 2 ECDHE-RSA-AES128-GCM-SHA256
 cipher 3 DHE-RSA-AES256-GCM-SHA384
 cipher 4 DHE-RSA-AES128-GCM-SHA256
```

> **Nota:** Durante las pruebas se identifico que cipher suites incorrectos causan el error "no shared cipher" y la conexion TLS falla. Es CRITICO usar estos cipher suites especificos.

**Configuracion TLS Profile:**

```
! TLS Profile para Microsoft
voice class tls-profile 1
 description Microsoft-ACS-Profile
 trustpoint <TRUSTPOINT_NAME>
 cipher 1
 tls-version TLSv1.2
 cn-san-validate server
 cn-san 1 *.communication.azure.com
 cn-san 2 sip.pstnhub.microsoft.com
```

**Configuracion SRTP:**

```
! SRTP Crypto Profile
voice class srtp-crypto 1
 crypto 1 AES_CM_128_HMAC_SHA1_80
```

#### 4.1.3 Certificados Requeridos

| Tipo | Descripcion | Requisitos |
|------|-------------|------------|
| **Certificado del CUBE** | Certificado TLS para el SBC | - Emitido por CA publica (DigiCert, GlobalSign, etc.)<br>- CN o SAN debe coincidir con el FQDN registrado en ACS<br>- Algoritmo RSA 2048 bits minimo<br>- Validez minima 1 ano |
| **CA Root de Microsoft** | Para validar conexiones desde ACS | - Baltimore CyberTrust Root<br>- DigiCert Global Root G2 |

**Validar certificado:**
```
show crypto pki certificates <TRUSTPOINT>
```

#### 4.1.4 Configuracion SIP Trunk hacia ACS

```
! Dial-peer para Microsoft ACS
dial-peer voice 1000 voip
 description Microsoft-ACS-Direct-Routing
 destination-pattern +T
 session protocol sipv2
 session target dns:sip.pstnhub.microsoft.com
 session transport tcp tls
 voice-class sip srtp-crypto 1
 voice-class sip tls-profile 1
 voice-class sip options-keepalive
 dtmf-relay rtp-nte
 codec g711ulaw
 no vad

! Inbound dial-peer desde Microsoft
dial-peer voice 1001 voip
 description From-Microsoft-ACS
 session protocol sipv2
 session transport tcp tls
 incoming uri via <PATTERN_FOR_MICROSOFT_IPS>
 voice-class codec 1
 dtmf-relay rtp-nte
```

#### 4.1.5 DNS SRV Records

El CUBE debe poder resolver los siguientes registros DNS de Microsoft:

| Registro | Valor |
|----------|-------|
| sip.pstnhub.microsoft.com | Resolucion directa |
| sip2.pstnhub.microsoft.com | Failover |
| sip3.pstnhub.microsoft.com | Failover |

### 4.2 Cisco CUCM (Proveedor de Telefonia)

#### 4.2.1 Requerimientos para el Proveedor

El proveedor de telefonia que administra CUCM debe configurar:

| Configuracion | Descripcion |
|---------------|-------------|
| Route Pattern | Patron de ruta para enviar llamadas al CUBE |
| SIP Trunk | Trunk SIP entre CUCM y CUBE |
| Translation Pattern | Si se requiere manipulacion de digitos |
| Calling Party Transformation | Para el caller ID de OPTI |

#### 4.2.2 Informacion Requerida del Proveedor

Optinoc necesita la siguiente informacion del proveedor:

| Dato | Descripcion |
|------|-------------|
| Rangos de extension | Extensiones internas que OPTI puede llamar |
| Prefijos PSTN | Como marcar numeros externos |
| Caller ID permitidos | Restricciones de caller ID |

---

## 5. Requerimientos de Red y Seguridad

### 5.1 IPs Publicas de Microsoft Azure

#### 5.1.1 Rangos de IP para Senalizacion SIP

El firewall debe permitir conexiones **ENTRANTES y SALIENTES** a las siguientes IPs de Microsoft:

| Rango CIDR | Descripcion |
|------------|-------------|
| 52.112.0.0/14 | Microsoft 365 Media |
| 52.120.0.0/14 | Microsoft 365 Media |
| 52.122.0.0/15 | Azure Communication Services |

#### 5.1.2 IPs Especificas de SIP Signaling

| IP/FQDN | Puerto | Protocolo | Descripcion |
|---------|--------|-----------|-------------|
| sip.pstnhub.microsoft.com | 5061 | TCP/TLS | SIP Signaling primario |
| sip2.pstnhub.microsoft.com | 5061 | TCP/TLS | SIP Signaling secundario |
| sip3.pstnhub.microsoft.com | 5061 | TCP/TLS | SIP Signaling terciario |
| 52.114.148.0/32 | 5061 | TCP/TLS | IP especifica region |
| 52.114.132.46/32 | 5061 | TCP/TLS | IP especifica region |
| 52.114.75.24/32 | 5061 | TCP/TLS | IP especifica region |
| 52.114.76.76/32 | 5061 | TCP/TLS | IP especifica region |
| 52.114.7.24/32 | 5061 | TCP/TLS | IP especifica region |

> **Nota:** Las IPs especificas pueden variar. Microsoft publica la lista actualizada en: https://learn.microsoft.com/en-us/microsoft-365/enterprise/urls-and-ip-address-ranges

### 5.2 Reglas de Firewall Requeridas

#### 5.2.1 Trafico SIP (Senalizacion)

| Origen | Destino | Puerto | Protocolo | Direccion |
|--------|---------|--------|-----------|-----------|
| Cisco CUBE | 52.112.0.0/14 | 5061 | TCP | Saliente |
| Cisco CUBE | 52.120.0.0/14 | 5061 | TCP | Saliente |
| 52.112.0.0/14 | Cisco CUBE | 5061 | TCP | Entrante |
| 52.120.0.0/14 | Cisco CUBE | 5061 | TCP | Entrante |

#### 5.2.2 Trafico RTP (Media/Audio)

| Origen | Destino | Puerto | Protocolo | Direccion |
|--------|---------|--------|-----------|-----------|
| Cisco CUBE | 52.112.0.0/14 | 1024-65535 | UDP | Saliente |
| Cisco CUBE | 52.120.0.0/14 | 1024-65535 | UDP | Saliente |
| 52.112.0.0/14 | Cisco CUBE | 1024-65535 | UDP | Entrante |
| 52.120.0.0/14 | Cisco CUBE | 1024-65535 | UDP | Entrante |

> **Recomendacion:** Para produccion, se puede restringir el rango UDP a los puertos configurados en el CUBE (ej: 16384-32767).

### 5.3 IP Publica Dedicada para CUBE

#### 5.3.1 Requisitos

| Requisito | Descripcion |
|-----------|-------------|
| IP Publica Fija | El CUBE debe tener una IP publica estatica |
| NAT | Si hay NAT, debe ser 1:1 (no PAT) |
| Reverse DNS | Recomendado configurar PTR record |
| Sin restricciones | No debe estar en listas negras |

#### 5.3.2 Registro DNS

| Registro | Tipo | Valor |
|----------|------|-------|
| sbc.bancooccidente.com.co | A | <IP_PUBLICA_CUBE> |

> Este FQDN es el que se registra en Azure Communication Services como SBC.

### 5.4 Certificados

#### 5.4.1 Certificado TLS para el CUBE

| Atributo | Requisito |
|----------|-----------|
| Tipo | X.509 v3 |
| CA Emisora | CA publica reconocida (DigiCert, GlobalSign, Comodo, etc.) |
| Common Name (CN) | sbc.bancooccidente.com.co |
| Subject Alternative Name (SAN) | sbc.bancooccidente.com.co |
| Key Algorithm | RSA 2048 bits o superior |
| Signature Algorithm | SHA-256 o superior |
| Validez | Minimo 1 ano |
| Extended Key Usage | Server Authentication, Client Authentication |

#### 5.4.2 Cadena de Certificados

El CUBE debe tener instalada la cadena completa:
1. Certificado del servidor (CUBE)
2. Certificado intermedio (CA intermedia)
3. Certificado raiz (CA raiz) - opcional pero recomendado

#### 5.4.3 Validacion del Certificado

Antes de la integracion, validar el certificado con:

```bash
openssl s_client -connect sbc.bancooccidente.com.co:5061 -showcerts
```

Debe mostrar:
- Certificado valido
- Cadena completa
- Fecha de expiracion futura

---

## 6. Accesos Requeridos

### 6.1 Accesos para Optinoc

#### 6.1.1 Azure / Microsoft 365

| Acceso | Descripcion | Justificacion |
|--------|-------------|---------------|
| Azure Portal - Contributor en ACS | Acceso al recurso Azure Communication Services | Configurar Direct Routing, voice routes, gestionar numeros |
| Azure Portal - Contributor en Azure OpenAI | Acceso al recurso Azure OpenAI | Configurar modelos, deployments |
| Microsoft 365 Admin Center | Acceso de lectura | Verificar licencias de Teams Phone |
| Teams Admin Center | Acceso de lectura | Verificar configuracion de Direct Routing |

#### 6.1.2 APIs y Connection Strings

| Credencial | Descripcion | Uso |
|------------|-------------|-----|
| ACS Connection String | Cadena de conexion del recurso ACS | Autenticacion de OPTI para hacer llamadas |
| Azure OpenAI API Key | Clave de API | Conexion a GPT-4o Realtime |
| Azure OpenAI Endpoint | URL del recurso | Conexion a GPT-4o Realtime |

#### 6.1.3 Acceso CLI (Opcional pero Recomendado)

Para automatizacion y troubleshooting:

```bash
# Azure CLI con permisos de Contributor en:
# - Resource Group de ACS
# - Resource Group de Azure OpenAI

az login
az account set --subscription <SUBSCRIPTION_ID>
```

### 6.2 Accesos para Banco de Occidente

#### 6.2.1 Cisco CUBE

| Acceso | Descripcion | Quien lo necesita |
|--------|-------------|-------------------|
| SSH al CUBE | Acceso CLI al router/SBC | Equipo de redes del banco |
| ASDM/Web UI | Si aplica | Equipo de redes del banco |
| Logs SIP | Acceso a logs de senalizacion | Troubleshooting conjunto |

**Comandos utiles para troubleshooting:**
```
debug ccsip messages
debug voip ccapi inout
show sip-ua status
show sip-ua connections tcp tls detail
show crypto pki certificates
```

#### 6.2.2 Acceso a Logs (Troubleshooting Conjunto)

Durante la implementacion y troubleshooting, se requiere que el banco pueda compartir:

| Log | Ubicacion | Proposito |
|-----|-----------|-----------|
| SIP Debug del CUBE | `debug ccsip messages` | Analizar senalizacion |
| TLS Debug | `debug crypto pki` | Problemas de certificados |
| Firewall Logs | Palo Alto/Fortinet/etc. | Verificar trafico permitido |

### 6.3 Coordinacion con Proveedor de Telefonia (CUCM)

#### 6.3.1 Informacion Requerida del Proveedor

| Dato | Descripcion |
|------|-------------|
| Diagrama de enrutamiento | Como fluyen las llamadas CUCM ↔ CUBE |
| Configuracion SIP Trunk | Trunk entre CUCM y CUBE |
| Codecs soportados | G.711, G.729, etc. |
| DTMF Method | RFC2833, SIP INFO, etc. |

#### 6.3.2 Configuraciones que debe hacer el Proveedor

| Configuracion | Descripcion |
|---------------|-------------|
| Route Pattern para OPTI | Patron que enruta llamadas entrantes desde ACS al destino correcto |
| Caller ID Translation | Configurar el caller ID de OPTI |
| SIP Trunk Permissions | Permitir trafico desde el CUBE |

---

## 7. Matriz de Responsabilidades

### 7.1 RACI Matrix

| Actividad | Optinoc | Banco TI | Banco Redes | Proveedor Tel. |
|-----------|---------|----------|-------------|----------------|
| **Azure Communication Services** |
| Crear recurso ACS | R/A | C | I | I |
| Configurar Direct Routing | R/A | C | I | I |
| Registrar SBC en ACS | R/A | C | C | I |
| **Azure OpenAI** |
| Solicitar acceso Azure OpenAI | R | A | I | I |
| Crear recurso y deployment | R/A | C | I | I |
| **Microsoft Teams** |
| Asignar licencias Teams Phone | C | R/A | I | I |
| Verificar usuarios habilitados | C | R/A | I | I |
| **Cisco CUBE** |
| Configurar TLS/Certificados | C | C | R/A | I |
| Configurar SIP Trunk a ACS | C | C | R/A | I |
| Configurar Cipher Suites | R | C | A | I |
| Instalar certificado publico | I | C | R/A | I |
| **Cisco CUCM** |
| Configurar Route Patterns | I | C | I | R/A |
| Configurar SIP Trunk CUCM-CUBE | I | C | C | R/A |
| **Red/Firewall** |
| Abrir puertos hacia Microsoft | C | C | R/A | I |
| Configurar IP publica | I | C | R/A | I |
| Configurar DNS | I | C | R/A | I |
| **Desarrollo OPTI** |
| Desarrollar aplicacion OPTI | R/A | I | I | I |
| Integrar con ACS | R/A | C | I | I |
| Integrar con Azure OpenAI | R/A | I | I | I |
| **Testing** |
| Pruebas de conectividad SIP | R | C | A | C |
| Pruebas de llamadas Teams | R | A | C | I |
| Pruebas de llamadas PSTN | R | C | C | A |
| Pruebas end-to-end | R/A | C | C | C |

**Leyenda:**
- **R** = Responsable (quien hace el trabajo)
- **A** = Accountable (quien aprueba/responde)
- **C** = Consultado
- **I** = Informado

---

## 8. Anexos Tecnicos

### 8.1 Comandos Azure CLI para Direct Routing

#### Crear recurso ACS
```bash
az communication create \
  --name acs-opti-bocc \
  --resource-group rg-opti-bocc \
  --location eastus \
  --data-location unitedstates
```

#### Registrar SBC
```bash
az communication phonenumbers direct-routing sbc create \
  --resource-group rg-opti-bocc \
  --name acs-opti-bocc \
  --fqdn sbc.bancooccidente.com.co \
  --sip-signaling-port 5061
```

#### Crear Voice Route
```bash
az communication phonenumbers direct-routing voice-route create \
  --resource-group rg-opti-bocc \
  --name acs-opti-bocc \
  --route-name "Colombia-Mobile" \
  --number-pattern "^\+573(\d{9})$" \
  --sbc-fqdn sbc.bancooccidente.com.co \
  --priority 1

az communication phonenumbers direct-routing voice-route create \
  --resource-group rg-opti-bocc \
  --name acs-opti-bocc \
  --route-name "Colombia-Fixed" \
  --number-pattern "^\+57[1-8](\d{7})$" \
  --sbc-fqdn sbc.bancooccidente.com.co \
  --priority 2
```

### 8.2 Configuracion Ejemplo Cisco CUBE

```
! === CONFIGURACION EJEMPLO CISCO CUBE PARA ACS ===
! IOS XE 16.09.01

! 1. Configurar crypto PKI trustpoint para certificado
crypto pki trustpoint ACS-TRUSTPOINT
 enrollment terminal
 revocation-check none
 rsakeypair ACS-KEYS 2048

! 2. Importar certificado (despues de obtenerlo de la CA)
crypto pki authenticate ACS-TRUSTPOINT
crypto pki import ACS-TRUSTPOINT certificate

! 3. TLS Profile
voice class tls-cipher 1
 cipher 1 ECDHE-RSA-AES256-GCM-SHA384
 cipher 2 ECDHE-RSA-AES128-GCM-SHA256

voice class tls-profile 1
 trustpoint ACS-TRUSTPOINT
 cipher 1
 cn-san-validate server
 cn-san 1 *.communication.azure.com
 cn-san 2 sip.pstnhub.microsoft.com

! 4. SRTP Crypto
voice class srtp-crypto 1
 crypto 1 AES_CM_128_HMAC_SHA1_80

! 5. Voice Class para Microsoft
voice class sip-profiles 100
 rule 1 request ANY sip-header Contact modify "<sip:(.*)>" "<sip:\1;transport=tls>"

! 6. Dial-peer saliente a Microsoft
dial-peer voice 1000 voip
 description TO-MICROSOFT-ACS
 destination-pattern +T
 session protocol sipv2
 session target dns:sip.pstnhub.microsoft.com
 session transport tcp tls
 voice-class sip tls-profile 1
 voice-class sip srtp-crypto 1
 voice-class sip profiles 100
 voice-class sip options-keepalive
 dtmf-relay rtp-nte
 codec g711ulaw
 no vad

! 7. Dial-peer entrante desde Microsoft
dial-peer voice 1001 voip
 description FROM-MICROSOFT-ACS
 session protocol sipv2
 session transport tcp tls
 voice-class sip tls-profile 1
 voice-class sip srtp-crypto 1
 incoming uri via MICROSOFT-PATTERN
 codec g711ulaw
 dtmf-relay rtp-nte

! 8. URI Pattern para identificar trafico de Microsoft
voice class uri MICROSOFT-PATTERN sip
 host ipv4:52.114.0.0
 host ipv4:52.112.0.0
```

### 8.3 Checklist de Verificacion Pre-Produccion

#### Azure
- [ ] Recurso ACS creado
- [ ] SBC registrado en Direct Routing
- [ ] Estado del SBC: "Online"
- [ ] Voice Routes configurados
- [ ] Connection String obtenido
- [ ] Recurso Azure OpenAI creado
- [ ] Modelo gpt-4o-realtime desplegado
- [ ] API Key obtenida

#### Microsoft Teams
- [ ] 50 usuarios con licencia Teams Phone
- [ ] Usuarios pueden hacer llamadas en Teams

#### Cisco CUBE
- [ ] Certificado TLS instalado y valido
- [ ] Cipher suites configurados correctamente
- [ ] SIP Trunk a ACS configurado
- [ ] OPTIONS keepalive funcionando
- [ ] SRTP habilitado

#### Red/Firewall
- [ ] IP publica asignada al CUBE
- [ ] DNS A record configurado
- [ ] Puertos 5061 TCP abiertos (entrada/salida)
- [ ] Puertos UDP 1024-65535 abiertos (entrada/salida)
- [ ] IPs de Microsoft permitidas

#### CUCM (Proveedor)
- [ ] Route Pattern configurado
- [ ] SIP Trunk CUCM-CUBE funcionando
- [ ] Caller ID configurado

### 8.4 Troubleshooting Comun

| Problema | Causa Probable | Solucion |
|----------|----------------|----------|
| SBC estado "Offline" en ACS | Certificado invalido o cipher incorrecto | Verificar certificado y cipher suites |
| "No shared cipher" | Cipher suites incompatibles | Configurar ECDHE-RSA-AES256-GCM-SHA384 |
| Llamada no conecta | Firewall bloqueando | Verificar reglas de firewall |
| Audio unidireccional | SRTP no configurado o NAT | Verificar SRTP y NAT settings |
| Caller ID incorrecto | Translation pattern faltante | Configurar en CUCM |

### 8.5 Contactos y Escalacion

| Rol | Responsable | Contacto |
|-----|-------------|----------|
| Lider Tecnico Optinoc | [Nombre] | [Email/Tel] |
| Administrador Azure Banco | [Nombre] | [Email/Tel] |
| Administrador Redes Banco | [Nombre] | [Email/Tel] |
| Proveedor Telefonia | [Nombre] | [Email/Tel] |

---

## Control de Versiones

| Version | Fecha | Autor | Cambios |
|---------|-------|-------|---------|
| 1.0 | Febrero 2026 | Optinoc | Version inicial |

---

*Documento generado para el proyecto OPTI - Banco de Occidente*
