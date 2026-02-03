# Estado del PoC - SBC Simulado con Azure ACS Direct Routing

> **Ultima actualizacion:** 2026-02-03
> **Estado:** En progreso - Kamailio configurado, pendiente verificar Azure

---

## Resumen de lo Completado

### 1. EC2 en AWS ✅
- **IP:** 35.171.83.237
- **Tipo:** t3.small (2 vCPU, 2GB RAM)
- **OS:** Ubuntu 22.04
- **SSH:** `ssh -i ~/opti-freepbx.pem ubuntu@35.171.83.237`

### 2. FreePBX en Docker ✅
- Corriendo en el contenedor `freepbx-sbc`
- IP interna: 172.18.0.2
- Puertos: 5060 UDP/TCP (SIP), 8080 (Web Admin)
- **Nota:** Puerto 5061 removido del docker-compose (Kamailio lo usa)

### 3. DNS en Cloudflare ✅
- `sbc.adrianpabonmendoza.com` → 35.171.83.237
- Proxy: OFF (nube gris)

### 4. Certificado Let's Encrypt ✅
- Ubicacion host: `/etc/letsencrypt/live/sbc.adrianpabonmendoza.com/`
- Copia para Kamailio: `/etc/kamailio/certs/`
- CN: sbc.adrianpabonmendoza.com
- Emisor: Let's Encrypt E7

### 5. Kamailio como SIP Proxy ✅
- **Por que Kamailio:** Asterisk/FreePBX pone la IP en los headers Via/Contact, Microsoft espera el FQDN
- **Kamailio soluciona:** Intercepta el trafico TLS, responde con FQDN en headers
- **Estado:** Corriendo en puerto 5061 TLS
- **Configuracion:** `/etc/kamailio/kamailio.cfg`

---

## Arquitectura Actual

```
Microsoft ACS ←─TLS 5061─→ Kamailio ←─UDP 5060─→ FreePBX ←─TCP─→ Twilio
                              │
                    (responde OPTIONS
                     con FQDN correcto)
```

---

## Problema Encontrado y Solucion

### Problema Original
Asterisk/PJSIP siempre pone la IP (35.171.83.237) en los headers SIP:
```
Via: SIP/2.0/TLS 35.171.83.237:5061
Contact: <sip:xxx@35.171.83.237:5061>
```

Microsoft rechazaba con error:
```
403 Forbidden - SBC certificate is not issued correctly.
Provided trunk FQDN '35.171.83.237' is not included in certificate's CN
```

### Solucion Implementada
Kamailio como proxy TLS que:
1. Escucha en puerto 5061 con certificado Let's Encrypt
2. Responde a OPTIONS con el FQDN correcto
3. Reescribe headers para usar FQDN en lugar de IP

---

## Configuracion Actual de Kamailio

Archivo: `/etc/kamailio/kamailio.cfg`

```kamailio
#!KAMAILIO
enable_tls=yes
listen=tls:0.0.0.0:5061

loadmodule "tls.so"
modparam("tls", "config", "/etc/kamailio/tls.cfg")

request_route {
    # Handle OPTIONS - respond with FQDN
    if (is_method("OPTIONS")) {
        append_hf("Contact: <sip:sbc.adrianpabonmendoza.com:5061;transport=tls>\r\n");
        sl_send_reply("200", "OK");
        exit;
    }
    # Forward other traffic to FreePBX
    $du = "sip:172.18.0.2:5060";
    t_relay();
}
```

Archivo: `/etc/kamailio/tls.cfg`
```
[server:default]
method = TLSv1.2
certificate = /etc/kamailio/certs/fullchain.pem
private_key = /etc/kamailio/certs/privkey.pem
verify_certificate = no
```

---

## Lo Que Falta Por Hacer

### 1. Verificar Estado en Azure Portal ⏳
- Ir a Azure Portal → Communication Services → Direct Routing
- El SBC deberia mostrar estado "Online" o "TLS: OK"
- Si sigue en "Unknown", ver siguiente paso

### 2. Si Azure Sigue en Unknown
Opciones:
a) **Agregar envio periodico de OPTIONS:** Kamailio debe enviar OPTIONS a Microsoft cada 60 segundos (requiere modulos rtimer + uac)
b) **Usar script cron:** Enviar OPTIONS manualmente via openssl cada minuto

### 3. Configurar Trunk en FreePBX para Microsoft
Una vez Azure este Online:
1. Crear trunk en FreePBX que apunte a Kamailio (172.18.0.1:5061)
2. Kamailio reenviara a Microsoft con headers correctos

### 4. Probar Llamada Completa
```
API Python → ACS → Direct Routing → Kamailio → FreePBX → Twilio → PSTN
```

---

## Comandos Utiles

### Verificar Kamailio
```bash
# Estado
sudo systemctl status kamailio

# Logs
sudo tail -f /var/log/syslog | grep kamailio

# Reiniciar
sudo systemctl restart kamailio

# Verificar TLS
echo | openssl s_client -connect sbc.adrianpabonmendoza.com:5061 2>/dev/null | openssl x509 -noout -subject
```

### FreePBX
```bash
cd ~/optinoc-bocc-realtime/poc-sbc-simulado
docker compose ps
docker compose logs -f
docker exec -it freepbx-sbc asterisk -rvvv
```

### Probar OPTIONS a Microsoft (con certificado)
```bash
sudo bash -c 'echo "OPTIONS sip:sip.pstnhub.microsoft.com:5061 SIP/2.0
Via: SIP/2.0/TLS sbc.adrianpabonmendoza.com:5061;branch=z9hG4bK-test
From: <sip:sbc.adrianpabonmendoza.com>;tag=test
To: <sip:sip.pstnhub.microsoft.com>
Call-ID: test@sbc.adrianpabonmendoza.com
CSeq: 1 OPTIONS
Contact: <sip:sbc.adrianpabonmendoza.com:5061;transport=tls>
Max-Forwards: 70
Content-Length: 0

" | timeout 10 openssl s_client -connect sip.pstnhub.microsoft.com:5061 -cert /etc/kamailio/certs/fullchain.pem -key /etc/kamailio/certs/privkey.pem -quiet 2>&1'
```

---

## Credenciales y Accesos

### AWS EC2
- SSH Key: `~/opti-freepbx.pem`
- Usuario: ubuntu
- IP: 35.171.83.237

### Cloudflare
- Dominio: adrianpabonmendoza.com
- DNS: sbc.adrianpabonmendoza.com → 35.171.83.237

### Twilio
- Numero: +19034994580
- SIP Trunk: optinoc-poc
- Termination User: freepbx-user
- Termination Pass: Opting0c2026!

### Azure ACS
- SBC registrado: sbc.adrianpabonmendoza.com:5061
- Voice Route: ^\+57(\d+)$ → sbc.adrianpabonmendoza.com

---

## Security Groups AWS (Puertos Abiertos)

| Puerto | Protocolo | Uso |
|--------|-----------|-----|
| 22 | TCP | SSH |
| 80 | TCP | Let's Encrypt / HTTP |
| 5060 | TCP/UDP | SIP (Twilio) |
| 5061 | TCP | SIP TLS (Azure ACS) |
| 8080 | TCP | FreePBX Web Admin |
| 10000-20000 | UDP | RTP Audio |

---

## Proximos Pasos para Nueva Sesion

1. **Verificar Azure Portal** - Ver si SBC esta Online
2. **Si esta Unknown** - Configurar envio periodico de OPTIONS desde Kamailio
3. **Si esta Online** - Configurar trunk en FreePBX y probar llamada
4. **Documentar** - Actualizar este archivo con resultados

---

## Archivos Importantes en EC2

| Archivo | Descripcion |
|---------|-------------|
| `/etc/kamailio/kamailio.cfg` | Configuracion principal Kamailio |
| `/etc/kamailio/tls.cfg` | Configuracion TLS Kamailio |
| `/etc/kamailio/certs/` | Certificados Let's Encrypt |
| `~/optinoc-bocc-realtime/poc-sbc-simulado/` | Directorio del PoC |

---

*Documento actualizado: 2026-02-03 01:35 UTC*
