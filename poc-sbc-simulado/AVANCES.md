# Avances PoC SBC Simulado

> **Última actualización:** 2026-01-29
> **Estado:** En progreso - Tunnel configurado, falta configurar trunks

---

## Resumen de lo Completado

### 1. FreePBX en Docker ✅

**Estado:** Corriendo

```bash
# Iniciar
cd /mnt/c/Users/Adrian/Documents/GitHub/optinoc-bocc-realtime/poc-sbc-simulado
docker compose up -d

# Verificar
docker compose ps
docker exec freepbx-sbc asterisk -rx "core show version"

# Acceso web
http://localhost:8080/admin
```

**Credenciales FreePBX:** (las que configuraste en el wizard inicial)

**Puertos expuestos:**
| Puerto | Protocolo | Uso |
|--------|-----------|-----|
| 5060 | UDP/TCP | SIP (Twilio) |
| 5061 | TCP | SIP TLS (Azure ACS) |
| 10000-10100 | UDP | RTP (audio) |
| 8080 | TCP | Web Admin |
| 8443 | TCP | Web Admin HTTPS |

---

### 2. Cloudflare Tunnel ✅

**Estado:** Configurado y conectado

**Tunnel:** `sbc-poc`
**ID:** `76cc3351-c3d4-42bc-aeaa-fd0224215444`

**Archivo de credenciales:**
```
/home/adrian/.cloudflared/76cc3351-c3d4-42bc-aeaa-fd0224215444.json
```

**Archivo de configuración:**
```
/home/adrian/.cloudflared/config-sbc.yml
```

**Contenido de config-sbc.yml:**
```yaml
tunnel: 76cc3351-c3d4-42bc-aeaa-fd0224215444
credentials-file: /home/adrian/.cloudflared/76cc3351-c3d4-42bc-aeaa-fd0224215444.json

ingress:
  # SIP TCP para Twilio (puerto 5060)
  - hostname: sip.adrianpabonmendoza.com
    service: tcp://localhost:5060

  # SIP TLS para Azure ACS (puerto 5061)
  - hostname: sbc.adrianpabonmendoza.com
    service: tcp://localhost:5061

  # Fallback
  - service: http_status:404
```

**Rutas DNS configuradas:**
| Subdominio | Tunnel | Uso |
|------------|--------|-----|
| sbc.adrianpabonmendoza.com | sbc-poc | Azure ACS (TLS 5061) |
| sip.adrianpabonmendoza.com | sbc-poc | Twilio (TCP 5060) |

**Comandos para el tunnel:**
```bash
# Iniciar tunnel
nohup cloudflared tunnel --config ~/.cloudflared/config-sbc.yml run sbc-poc > /tmp/sbc-tunnel.log 2>&1 &

# Ver logs
cat /tmp/sbc-tunnel.log

# Ver estado
cloudflared tunnel info sbc-poc

# Detener
pkill -f "cloudflared.*sbc-poc"
```

---

### 3. Certificados SSL ✅

**Estado:** Generados (autofirmados para PoC)

```bash
# Ubicación
/mnt/c/Users/Adrian/Documents/GitHub/optinoc-bocc-realtime/poc-sbc-simulado/certs/
├── cert.pem
└── key.pem
```

**Nota:** Para producción con Azure ACS se necesita certificado de CA pública.

---

## Pendiente por Configurar

### 4. Twilio ⏳

**Pasos:**
1. Crear cuenta en https://www.twilio.com (si no tienes)
2. Comprar número Colombia (+57) o USA (+1)
3. Crear Elastic SIP Trunk:
   - Ir a **Elastic SIP Trunking** → **Trunks** → **Create**
   - Nombre: `optinoc-poc`

4. Configurar **Origination** (Twilio → FreePBX):
   ```
   Origination URI: sip:sip.adrianpabonmendoza.com:5060;transport=tcp
   ```

5. Configurar **Termination** (FreePBX → Twilio):
   - Crear Termination URI: `optinoc-poc.pstn.twilio.com`
   - Crear credenciales (username/password)

6. Asociar número al trunk

**Guardar aquí las credenciales cuando las tengas:**
```
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
TWILIO_SIP_DOMAIN=optinoc-poc.pstn.twilio.com
TWILIO_SIP_USER=
TWILIO_SIP_PASS=
```

---

### 5. Trunk Twilio en FreePBX ⏳

**Pasos en http://localhost:8080/admin:**

1. **Connectivity** → **Trunks** → **Add Trunk** → **Add SIP (chan_pjsip) Trunk**

2. **General:**
   - Trunk Name: `twilio-trunk`
   - Outbound CallerID: `+57XXXXXXXXXX` (tu número Twilio)

3. **pjsip Settings → General:**
   ```
   Username: [TWILIO_SIP_USER]
   Secret: [TWILIO_SIP_PASS]
   Authentication: Outbound
   Registration: Send
   SIP Server: optinoc-poc.pstn.twilio.com
   SIP Server Port: 5060
   Transport: TCP  ← IMPORTANTE: TCP no UDP
   ```

4. **pjsip Settings → Advanced:**
   ```
   From Domain: optinoc-poc.pstn.twilio.com
   ```

5. **Submit** y **Apply Config**

---

### 6. Azure ACS - Direct Routing ⏳

**Pasos en Azure Portal:**

1. Ir a tu recurso **Azure Communication Services**
2. **Direct Routing** → **Session Border Controllers** → **Add**
3. Configurar:
   ```
   FQDN: sbc.adrianpabonmendoza.com
   Puerto: 5061
   ```
4. Click **Add**

5. **Voice Routes** → **Add**:
   ```
   Name: Colombia-Route
   Number Pattern: ^\+57(\d+)$
   SBC: sbc.adrianpabonmendoza.com
   Priority: 1
   ```

6. Esperar ~15 minutos hasta que el estado sea **Online**

---

### 7. Rutas en FreePBX ⏳

**Ruta Entrante (desde Twilio/PSTN):**
1. **Connectivity** → **Inbound Routes** → **Add**
2. Description: `Desde PSTN`
3. DID Number: (dejar vacío para cualquier número)
4. Destination: (extensión o IVR de prueba)

**Ruta Saliente (hacia PSTN via Twilio):**
1. **Connectivity** → **Outbound Routes** → **Add**
2. Route Name: `Hacia PSTN`
3. Dial Patterns:
   - `+57XXXXXXXXXX` (Colombia)
   - `+1XXXXXXXXXX` (USA)
4. Trunk Sequence: `twilio-trunk`

---

## Comandos Útiles

### Docker
```bash
# Iniciar todo
cd /mnt/c/Users/Adrian/Documents/GitHub/optinoc-bocc-realtime/poc-sbc-simulado
docker compose up -d

# Ver logs
docker compose logs -f freepbx

# CLI de Asterisk
docker exec -it freepbx-sbc asterisk -rvvv

# Reiniciar
docker compose restart freepbx

# Detener
docker compose down

# Detener y borrar datos (empezar de cero)
docker compose down -v
```

### Cloudflare Tunnel
```bash
# Iniciar
nohup cloudflared tunnel --config ~/.cloudflared/config-sbc.yml run sbc-poc > /tmp/sbc-tunnel.log 2>&1 &

# Ver logs
tail -f /tmp/sbc-tunnel.log

# Detener
pkill -f "cloudflared.*sbc-poc"

# Listar tunnels
cloudflared tunnel list
```

### Asterisk (dentro de FreePBX)
```bash
# Entrar al CLI
docker exec -it freepbx-sbc asterisk -rvvv

# Comandos útiles dentro del CLI:
pjsip show endpoints          # Ver endpoints SIP
pjsip show registrations      # Ver registros (Twilio)
core show channels            # Ver llamadas activas
sip set debug on              # Activar debug SIP
core restart now              # Reiniciar Asterisk
```

---

## Arquitectura Final

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TU PC (Docker + WSL)                            │
│                                                                              │
│  ┌────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐   │
│  │   FreePBX      │    │   Cloudflare    │    │   API OPTI              │   │
│  │   (Asterisk)   │◄──►│   Tunnel        │    │   (cuando esté listo)   │   │
│  │                │    │   sbc-poc       │    │                         │   │
│  │  :5060 (SIP)   │    │                 │    │  :8000                  │   │
│  │  :5061 (TLS)   │    │                 │    │                         │   │
│  └────────────────┘    └────────┬────────┘    └─────────────────────────┘   │
│                                 │                                            │
└─────────────────────────────────┼────────────────────────────────────────────┘
                                  │
                    ══════════════╪══════════════
                        INTERNET  │
                    ══════════════╪══════════════
                                  │
              ┌───────────────────┴───────────────────┐
              │                                       │
              ▼                                       ▼
      ┌───────────────┐                       ┌───────────────┐
      │    TWILIO     │                       │    AZURE      │
      │               │                       │    ACS        │
      │  sip.adrian...│                       │               │
      │  :5060 TCP    │                       │  sbc.adrian...│
      │               │                       │  :5061 TLS    │
      │  Número +57   │                       │               │
      └───────────────┘                       └───────────────┘
```

---

## Notas Importantes

1. **Cloudflare Tunnel no soporta UDP** - Por eso Twilio debe configurarse con `transport=tcp`

2. **El tunnel debe estar corriendo** para que las URLs funcionen

3. **FreePBX tarda ~5-10 min** en iniciar la primera vez

4. **Azure ACS tarda ~15 min** en mostrar el SBC como "Online"

5. **Para producción:** Reemplazar FreePBX por el Cisco CUBE real del cliente

---

## Problemas Conocidos y Soluciones

### FreePBX no inicia el servidor web
```bash
# Verificar logs
docker compose logs freepbx | tail -50

# Verificar Apache
docker exec freepbx-sbc netstat -tlnp | grep 80
```

### Tunnel no conecta
```bash
# Verificar proceso
ps aux | grep cloudflared

# Ver logs
cat /tmp/sbc-tunnel.log

# Reiniciar
pkill -f "cloudflared.*sbc-poc"
nohup cloudflared tunnel --config ~/.cloudflared/config-sbc.yml run sbc-poc > /tmp/sbc-tunnel.log 2>&1 &
```

### Error de base de datos en FreePBX
```bash
# Reiniciar desde cero
docker compose down -v
docker compose up -d
# Esperar 5-10 minutos
```
