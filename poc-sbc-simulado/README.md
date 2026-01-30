# PoC: Simulacion de Central Telefonica con FreePBX

> **Proposito:** Simular la infraestructura Cisco CUBE del cliente para demostrar Direct Routing con ACS.

## Arquitectura del PoC

```
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    TU COMPUTADOR (Docker)                                   │
│                                                                                             │
│   ┌──────────────────────────────────────────────────────────────────────────────────────┐  │
│   │                                                                                      │  │
│   │    ┌─────────────┐     ┌──────────────────────┐     ┌─────────────────────────┐     │  │
│   │    │   OPTI      │     │      FreePBX         │     │    Cloudflare Tunnel    │     │  │
│   │    │   (API)     │<───>│   (Simula CUBE)      │<───>│    (Expone SBC)         │     │  │
│   │    │             │     │                      │     │                         │     │  │
│   │    │  Puerto     │     │  - SIP UDP 5060      │     │  sbc.tudominio.com      │     │  │
│   │    │  8000       │     │  - SIP TLS 5061      │     │  -> localhost:5061      │     │  │
│   │    │             │     │  - RTP 10000-20000   │     │                         │     │  │
│   │    └─────────────┘     └──────────────────────┘     └─────────────────────────┘     │  │
│   │                                   │                                                  │  │
│   └───────────────────────────────────┼──────────────────────────────────────────────────┘  │
│                                       │                                                     │
└───────────────────────────────────────┼─────────────────────────────────────────────────────┘
                                        │
                    ════════════════════╪════════════════════
                            INTERNET    │
                    ════════════════════╪════════════════════
                                        │
                ┌───────────────────────┴───────────────────────┐
                │                                               │
                ▼                                               ▼
        ┌───────────────┐                               ┌───────────────┐
        │    TWILIO     │                               │    AZURE      │
        │               │                               │    ACS        │
        │  Numero +57   │                               │               │
        │  SIP Trunk    │                               │  Direct       │
        │  UDP 5060     │                               │  Routing      │
        │               │                               │  TLS 5061     │
        └───────────────┘                               └───────────────┘
```

## Requisitos Previos

- [ ] Docker Desktop instalado
- [ ] Cuenta de Twilio (crear en https://www.twilio.com)
- [ ] Cuenta de Cloudflare (gratis) con un dominio
- [ ] Azure Communication Services configurado

## Estructura del PoC

```
poc-sbc-simulado/
├── README.md                    # Este archivo
├── docker-compose.yml           # FreePBX + Asterisk
├── .env.example                 # Variables de entorno
├── config/
│   ├── sip-twilio.conf          # Trunk hacia Twilio
│   ├── sip-acs.conf             # Trunk hacia Azure ACS
│   └── extensions.conf          # Reglas de enrutamiento
├── certs/
│   └── .gitkeep                 # Certificados SSL (generados)
└── scripts/
    ├── setup.sh                 # Configuracion inicial
    ├── start.sh                 # Iniciar servicios
    ├── stop.sh                  # Detener servicios
    ├── test-twilio.sh           # Probar conexion Twilio
    └── test-acs.sh              # Probar conexion ACS
```

---

## Paso 1: Configurar Twilio

### 1.1 Crear cuenta y comprar numero

1. Ir a https://www.twilio.com y crear cuenta
2. Ir a **Phone Numbers** > **Buy a number**
3. Seleccionar Colombia (+57) o USA (+1) para pruebas
4. Costo: ~$1-2 USD/mes

### 1.2 Crear SIP Trunk (Elastic SIP Trunking)

1. Ir a **Elastic SIP Trunking** > **Trunks**
2. Click **Create new SIP Trunk**
3. Nombre: `optinoc-poc`

### 1.3 Configurar Origination (Twilio -> FreePBX)

En la pestana **Origination**:

```
Origination URI: sip:tu-ip-publica:5060
# O si usas Cloudflare Tunnel:
Origination URI: sip:sbc-poc.tudominio.com:5060
```

### 1.4 Configurar Termination (FreePBX -> Twilio)

En la pestana **Termination**:

1. Click **Add new Termination URI**
2. Termination URI: `optinoc-poc.pstn.twilio.com`
3. Crear credenciales:
   - Username: `optinoc-user`
   - Password: `contraseña-segura` (generada por Twilio)

### 1.5 Asociar numero al trunk

En **Phone Numbers** > tu numero > **Voice Configuration**:
- Configure with: **SIP Trunk**
- SIP Trunk: `optinoc-poc`

---

## Paso 2: Configurar Variables de Entorno

Copiar `.env.example` a `.env` y completar:

```bash
cp .env.example .env
```

Editar `.env`:

```bash
# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+573001234567
TWILIO_SIP_DOMAIN=optinoc-poc.pstn.twilio.com
TWILIO_SIP_USER=optinoc-user
TWILIO_SIP_PASS=contraseña-segura

# Cloudflare Tunnel (se genera en paso 3)
CLOUDFLARE_TUNNEL_TOKEN=xxxxxxxx

# Azure ACS
ACS_CONNECTION_STRING=endpoint=https://xxx.communication.azure.com/;accesskey=xxx

# Dominio para el SBC
SBC_FQDN=sbc-poc.tudominio.com
```

---

## Paso 3: Configurar Cloudflare Tunnel

El tunnel expone tu FreePBX local a internet con HTTPS/TLS automatico.

### 3.1 Instalar cloudflared

```bash
# Windows (PowerShell como Admin)
winget install --id Cloudflare.cloudflared

# Linux
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/
```

### 3.2 Autenticarse

```bash
cloudflared tunnel login
```

### 3.3 Crear tunnel

```bash
cloudflared tunnel create sbc-poc
```

Esto genera un archivo de credenciales en `~/.cloudflared/`

### 3.4 Configurar DNS

```bash
cloudflared tunnel route dns sbc-poc sbc-poc.tudominio.com
```

### 3.5 Crear archivo de configuracion

Crear `~/.cloudflared/config.yml`:

```yaml
tunnel: sbc-poc
credentials-file: /home/tu-usuario/.cloudflared/<tunnel-id>.json

ingress:
  # SIP TLS para ACS (TCP)
  - hostname: sbc-poc.tudominio.com
    service: tcp://localhost:5061
  # WebSocket/HTTPS para callbacks
  - hostname: api-poc.tudominio.com
    service: http://localhost:8000
  - service: http_status:404
```

**Nota importante sobre SIP:** Cloudflare Tunnel no soporta UDP directamente. Para el SIP de Twilio (UDP 5060) necesitas una de estas opciones:

1. **IP publica directa** - Si tu router soporta port forwarding
2. **Usar TCP para Twilio** - Twilio soporta SIP sobre TCP
3. **Ngrok con UDP** - `ngrok udp 5060`

---

## Paso 4: Levantar FreePBX con Docker

### 4.1 Iniciar servicios

```bash
cd poc-sbc-simulado
docker-compose up -d
```

### 4.2 Acceder a la interfaz web

- URL: http://localhost:8080
- Usuario: admin
- Password: (definida en docker-compose)

### 4.3 Configuracion inicial de FreePBX

1. Ir a **Admin** > **System Admin** > Activar FreePBX
2. Ir a **Connectivity** > **Trunks**

---

## Paso 5: Configurar Trunks en FreePBX

### 5.1 Trunk hacia Twilio (SIP UDP 5060)

En FreePBX web:

1. **Connectivity** > **Trunks** > **Add Trunk** > **Add SIP (chan_pjsip) Trunk**

2. **General**:
   - Trunk Name: `twilio-trunk`
   - Outbound CallerID: `+573001234567`

3. **pjsip Settings** > **General**:
   ```
   Username: optinoc-user
   Secret: contraseña-segura
   Authentication: Outbound
   Registration: Send
   SIP Server: optinoc-poc.pstn.twilio.com
   SIP Server Port: 5060
   ```

4. **pjsip Settings** > **Advanced**:
   ```
   From Domain: optinoc-poc.pstn.twilio.com
   ```

### 5.2 Trunk hacia Azure ACS (SIP TLS 5061)

1. **Connectivity** > **Trunks** > **Add Trunk** > **Add SIP (chan_pjsip) Trunk**

2. **General**:
   - Trunk Name: `acs-trunk`
   - Outbound CallerID: `+573001234567`

3. **pjsip Settings** > **General**:
   ```
   Username: (dejar vacio - ACS no usa autenticacion SIP)
   Authentication: None
   Registration: None
   SIP Server: sip.pstnhub.microsoft.com
   SIP Server Port: 5061
   Transport: TLS
   ```

4. **pjsip Settings** > **Advanced**:
   ```
   From Domain: sbc-poc.tudominio.com
   Match (Permit): 52.112.0.0/14,52.120.0.0/14
   ```

---

## Paso 6: Configurar Rutas (Dial Plans)

### 6.1 Ruta entrante desde ACS

En **Connectivity** > **Inbound Routes** > **Add Inbound Route**:

- Description: `Desde ACS`
- DID Number: `(cualquier)`
- Set Destination: `Misc Destinations` > `API OPTI` (o extension de prueba)

### 6.2 Ruta saliente hacia PSTN via Twilio

En **Connectivity** > **Outbound Routes** > **Add Outbound Route**:

- Route Name: `Hacia PSTN`
- Dial Patterns:
  - Match Pattern: `57XXXXXXXXXX` (Colombia)
  - Match Pattern: `1XXXXXXXXXX` (USA)
- Trunk Sequence: `twilio-trunk`

---

## Paso 7: Registrar SBC en Azure ACS

### 7.1 Via Azure Portal

1. Ir a tu recurso ACS > **Direct Routing** > **Session Border Controllers**
2. Click **Add**
3. Completar:
   - FQDN: `sbc-poc.tudominio.com`
   - SIP Port: `5061`
   - Click **Add**

### 7.2 Configurar Voice Routes

1. En **Direct Routing** > **Voice Routes** > **Add**
2. Completar:
   - Name: `Colombia-Route`
   - Number Pattern: `^\+57(\d+)$`
   - SBC: `sbc-poc.tudominio.com`
   - Priority: 1

### 7.3 Verificar estado

Esperar ~15 minutos. El estado debe cambiar a **Online**.

Si queda en **Pending** o **Offline**:
- Verificar que el tunnel esta corriendo
- Verificar certificado TLS
- Revisar logs de FreePBX

---

## Paso 8: Pruebas

### 8.1 Verificar conectividad

```bash
# Verificar que FreePBX esta corriendo
docker-compose ps

# Ver logs de Asterisk
docker-compose logs -f freepbx

# Verificar trunk Twilio
docker-compose exec freepbx asterisk -rx "pjsip show registrations"

# Verificar trunk ACS
docker-compose exec freepbx asterisk -rx "pjsip show endpoints"
```

### 8.2 Probar llamada Twilio -> FreePBX

1. Llamar al numero Twilio desde tu celular
2. Debe escucharse el IVR de FreePBX

### 8.3 Probar llamada ACS -> FreePBX

```bash
# Desde tu API OPTI
curl -X POST http://localhost:8000/calls/outbound \
  -H "Content-Type: application/json" \
  -d '{"target_number": "+573001234567"}'
```

### 8.4 Flujo completo

```
Tu celular <--PSTN--> Twilio <--SIP--> FreePBX <--SIP TLS--> ACS <--WebSocket--> OPTI
```

---

## Troubleshooting

### El trunk ACS no se conecta

1. Verificar FQDN resuelve correctamente:
   ```bash
   nslookup sbc-poc.tudominio.com
   ```

2. Verificar certificado TLS:
   ```bash
   openssl s_client -connect sbc-poc.tudominio.com:5061
   ```

3. Verificar firewall permite IPs de Microsoft:
   - 52.112.0.0/14
   - 52.120.0.0/14

### El trunk Twilio no registra

1. Verificar credenciales en Twilio Console
2. Ver logs SIP:
   ```bash
   docker-compose exec freepbx asterisk -rx "pjsip set logger on"
   ```

### No hay audio (one-way audio)

1. Verificar puertos RTP estan abiertos (10000-20000 UDP)
2. Si estas detras de NAT, configurar STUN:
   ```
   Admin > Settings > Asterisk SIP Settings > NAT
   External Address: tu-ip-publica
   ```

---

## Diferencias con Produccion

| Aspecto | PoC | Produccion |
|---------|-----|------------|
| SBC | FreePBX/Docker | Cisco CUBE del cliente |
| Certificado | Let's Encrypt | CA comercial del cliente |
| Numero | Twilio | Infraestructura cliente |
| Exposicion | Cloudflare Tunnel | IP publica dedicada |
| Soporte | Sin SLA | Con soporte Microsoft (si SBC certificado) |

---

## Costos Estimados del PoC

| Componente | Costo |
|------------|-------|
| Twilio numero | $1-2/mes |
| Twilio minutos | $0.01/min aprox |
| Cloudflare Tunnel | Gratis |
| Azure ACS | $0.004/min |
| FreePBX | Gratis (open source) |
| **Total mensual** | **~$5-10 para pruebas** |

---

## Siguiente Paso

Una vez validado el PoC, el cliente puede:

1. Reemplazar FreePBX por su Cisco CUBE real
2. Usar su numero telefonico existente
3. Configurar certificado TLS de su CA corporativa
4. Abrir firewall segun la guia `informacion_cisco_sbc_acs.md`
