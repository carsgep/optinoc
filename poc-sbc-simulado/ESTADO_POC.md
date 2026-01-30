# Estado del PoC - SBC Simulado con Azure ACS Direct Routing

> **Ultima actualizacion:** 2026-01-30
> **Objetivo:** Simular la infraestructura del cliente (Cisco CUBE) para probar Direct Routing con Azure ACS

---

## Resumen Ejecutivo

### Que estamos simulando

| Cliente Real | PoC (Simulacion) |
|--------------|------------------|
| Cisco CUBE (ASR1000, IOS XE 16.09.01) | FreePBX/Asterisk en Docker |
| CUCM 12.5.1 (proveedor telefonia) | Twilio (SIP Trunk) |
| Red PSTN del banco | Numero Twilio |
| Azure ACS Direct Routing | Azure ACS Direct Routing (mismo) |

### Arquitectura Objetivo del PoC

```
API Python → Azure ACS → Direct Routing → FreePBX → Twilio → PSTN → Telefono
   │              │              │            │          │
   │         (Microsoft)    (TLS 5061)   (simula CUBE) (simula PSTN)
   │                                         │
   └─────── OpenAI Realtime ←────────────────┘
```

---

## Estado Actual de Componentes

### 1. FreePBX en Docker ✅ FUNCIONANDO

**Ubicacion:** Tu PC local (WSL2)

```bash
cd /mnt/c/Users/Adrian/Documents/GitHub/optinoc-bocc-realtime/poc-sbc-simulado
docker compose up -d
```

**Acceso:** http://localhost:8080/admin

**Puertos:**
- 5060 UDP/TCP - SIP
- 5061 TCP - SIP TLS
- 10000-10100 UDP - RTP
- 8080/8443 - Web Admin

### 2. Twilio ✅ CONFIGURADO

**Numero:** +19034994580 (o +14846736495)

**SIP Trunk:** `optinoc-poc`

**Credenciales Termination:**
- Usuario: `freepbx-user`
- Password: `Opting0c2026!`
- Dominio: `optinoc-poc.pstn.twilio.com`

**Estado:** Llamadas entrantes funcionan (probado con bore.pub)

### 3. Exposicion a Internet

#### Cloudflare Tunnel ❌ NO FUNCIONA PARA SIP
- Tunnel `sbc-poc` creado
- DNS: sbc.adrianpabonmendoza.com, sip.adrianpabonmendoza.com
- **Problema:** Cloudflare Tunnel no pasa trafico SIP correctamente

#### bore.pub ✅ FUNCIONA PARA PRUEBAS
```bash
bore local 5060 --to bore.pub
```
- URL temporal: bore.pub:16816 (cambia cada vez)
- **Limitacion:** Solo TCP, sin TLS (no sirve para Azure ACS)

### 4. Azure ACS Direct Routing ❌ PENDIENTE

**Requisitos no cumplidos:**
- [ ] Servidor con IP publica fija
- [ ] FQDN publico apuntando al servidor
- [ ] Certificado TLS de CA publica (Let's Encrypt)
- [ ] FreePBX con TLS habilitado en puerto 5061

---

## Infraestructura del Cliente Real

Informacion recopilada:

| Componente | Detalle | Administrador |
|------------|---------|---------------|
| **CUCM** | Version 12.5.1.13900-152 | Proveedor telefonia |
| **CUBE** | IOS XE 16.09.01 (Fuji) | Banco de Occidente |
| **Plataforma** | ASR1000 | Banco |

**Alerta:** IOS XE 16.09.01 es anterior a la version recomendada (16.11+). Puede haber problemas con cipher suites TLS 1.2.

---

## Plan para Completar el PoC

### Fase 1: Crear VM en Azure

```bash
# Especificaciones
- Ubuntu 22.04 LTS
- Tamano: B1s o B2s
- IP publica estatica
- NSG: Abrir puertos 22, 5061 TCP, 10000-20000 UDP
```

### Fase 2: Configurar DNS en Cloudflare

```
Tipo: A
Nombre: sbc
Contenido: [IP de la VM]
Proxy: OFF (nube gris) <-- IMPORTANTE
```

### Fase 3: Obtener Certificado Let's Encrypt

```bash
# En la VM
sudo apt update && sudo apt install certbot -y
sudo certbot certonly --standalone -d sbc.adrianpabonmendoza.com
```

### Fase 4: Instalar FreePBX en la VM

```bash
# Clonar repo
git clone https://github.com/[tu-repo]/optinoc-bocc-realtime.git
cd optinoc-bocc-realtime/poc-sbc-simulado

# Copiar certificados
sudo cp /etc/letsencrypt/live/sbc.adrianpabonmendoza.com/fullchain.pem ./certs/cert.pem
sudo cp /etc/letsencrypt/live/sbc.adrianpabonmendoza.com/privkey.pem ./certs/key.pem

# Iniciar
docker compose up -d
```

### Fase 5: Configurar FreePBX para TLS

1. Acceder a http://[IP_VM]:8080/admin
2. Admin → Certificate Management → Import certificado
3. Settings → Asterisk SIP Settings → Enable TLS en puerto 5061
4. Trunk hacia Twilio (ya configurado, solo verificar)

### Fase 6: Registrar SBC en Azure ACS

```
Azure Portal → Communication Services → Direct Routing

1. Add SBC:
   FQDN: sbc.adrianpabonmendoza.com
   Port: 5061

2. Add Voice Route:
   Name: Colombia
   Pattern: ^\+57(\d+)$
   SBC: sbc.adrianpabonmendoza.com
   Priority: 1
```

### Fase 7: Configurar API Python

```bash
# .env
ACS_CONNECTION_STRING=endpoint=https://xxx.communication.azure.com/;accesskey=xxx
CALLBACK_URI=https://[URL_PUBLICA_API]/callbacks/acs
OPENAI_API_KEY=sk-xxx
ACS_PHONE_NUMBER=+19034994580  # Numero de Twilio para caller ID
```

### Fase 8: Probar Llamada

```bash
curl -X POST http://localhost:8000/calls/outbound \
  -H "Content-Type: application/json" \
  -d '{"target_number": "+573232257331"}'
```

---

## Archivos Importantes del Repositorio

| Archivo | Descripcion |
|---------|-------------|
| `CLAUDE.md` | Contexto general del proyecto |
| `poc-sbc-simulado/ESTADO_POC.md` | **ESTE ARCHIVO** - Estado actual del PoC |
| `poc-sbc-simulado/AVANCES.md` | Avances detallados (Cloudflare, FreePBX, etc.) |
| `poc-sbc-simulado/docker-compose.yml` | Configuracion Docker de FreePBX |
| `guia_reunion_cisco_cube_acs.md` | Guia tecnica completa Direct Routing |
| `informacion_cisco_sbc_acs.md` | Requisitos tecnicos del CUBE |
| `cuestionario_tecnico_banco.md` | Preguntas para el cliente |
| `requerimientos_banco_occidente.md` | Requerimientos formales |

---

## Credenciales y Configuraciones

### Cloudflare
- Dominio: `adrianpabonmendoza.com`
- Tunnel ID: `76cc3351-c3d4-42bc-aeaa-fd0224215444`
- Config: `~/.cloudflared/config-sbc.yml`

### Twilio
- Numero: +19034994580
- SIP Trunk: optinoc-poc
- Termination User: freepbx-user
- Termination Pass: Opting0c2026!
- Termination Domain: optinoc-poc.pstn.twilio.com

### FreePBX (local)
- URL: http://localhost:8080/admin
- Container: freepbx-sbc

---

## Comandos Utiles

### FreePBX Local
```bash
# Iniciar
cd /mnt/c/Users/Adrian/Documents/GitHub/optinoc-bocc-realtime/poc-sbc-simulado
docker compose up -d

# Logs
docker compose logs -f freepbx

# CLI Asterisk
docker exec -it freepbx-sbc asterisk -rvvv

# Detener
docker compose down
```

### bore (pruebas temporales)
```bash
bore local 5060 --to bore.pub
# Resultado: bore.pub:XXXXX (puerto aleatorio)
```

### Cloudflare Tunnel (no funciona para SIP pero esta configurado)
```bash
nohup cloudflared tunnel --config ~/.cloudflared/config-sbc.yml run sbc-poc > /tmp/sbc-tunnel.log 2>&1 &
```

---

## Problemas Conocidos y Soluciones

### 1. Cloudflare Tunnel no pasa SIP
**Solucion:** Usar VM con IP publica + Let's Encrypt

### 2. bore.pub no tiene TLS
**Solucion:** Solo para pruebas locales, no sirve para Azure ACS

### 3. IOS XE 16.09.01 del cliente
**Solucion:** Probar primero, si falla TLS actualizar a 16.11+

### 4. Twilio 403 Forbidden en llamadas salientes
**Causa:** Username incorrecto en trunk
**Solucion:** Verificar que el trunk use `freepbx-user` (no "Outbound")

---

## Siguiente Paso Inmediato

**Crear VM en Azure** y continuar con el plan de Fase 1 en adelante.

¿El usuario tiene la VM lista? Si no, crearla con:
- Ubuntu 22.04
- IP publica estatica
- Puertos: 22, 5061 TCP, 10000-20000 UDP

---

## Contacto

Para continuar este PoC en una nueva sesion de Claude Code:
1. Leer este archivo (`poc-sbc-simulado/ESTADO_POC.md`)
2. Leer `CLAUDE.md` para contexto general
3. El siguiente paso es crear/configurar la VM en Azure

---

*Documento actualizado: 2026-01-30*
