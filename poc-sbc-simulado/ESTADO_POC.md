# Estado del PoC - SBC Simulado con Azure ACS Direct Routing

> **Ultima actualizacion:** 2026-02-03 02:00 UTC
> **Estado:** SBC ONLINE en Azure - Listo para probar llamadas

---

## Resumen de lo Completado

### 1. EC2 en AWS ✅
- **IP:** 35.171.83.237
- **Tipo:** t3.small (2 vCPU, 2GB RAM)
- **OS:** Ubuntu 24.04
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
- **IMPORTANTE:** Debe ser tipo **RSA**, no ECDSA
- Ubicacion host: `/etc/letsencrypt/live/sbc.adrianpabonmendoza.com/`
- Copia para Kamailio: `/etc/kamailio/certs/`
- CN: sbc.adrianpabonmendoza.com
- Emisor: Let's Encrypt R12
- **Comando para regenerar como RSA:**
  ```bash
  sudo certbot certonly --standalone \
      -d sbc.adrianpabonmendoza.com \
      --cert-name sbc.adrianpabonmendoza.com \
      --key-type rsa \
      --rsa-key-size 2048 \
      --force-renewal
  ```

### 5. Kamailio como SIP Proxy ✅
- **Por que Kamailio:** Asterisk/FreePBX pone la IP en los headers Via/Contact, Microsoft espera el FQDN
- **Kamailio soluciona:** Intercepta el trafico TLS, responde con FQDN en headers
- **Estado:** Corriendo en puerto 5061 TLS
- **Configuracion:** `/etc/kamailio/kamailio.cfg`

### 6. Azure ACS Direct Routing ✅
- **SBC Status:** ONLINE
- **TLS Status:** OK
- **FQDN:** sbc.adrianpabonmendoza.com:5061

---

## Arquitectura Actual

```
Microsoft ACS ←─TLS 5061─→ Kamailio ←─UDP 5060─→ FreePBX ←─TCP─→ Twilio
                              │
                    (responde OPTIONS
                     con FQDN correcto)
```

---

## Problemas Encontrados y Soluciones

### Problema 1: Headers SIP con IP en lugar de FQDN
**Sintoma:** Microsoft rechazaba con 403 Forbidden
```
403 Forbidden - SBC certificate is not issued correctly.
Provided trunk FQDN '35.171.83.237' is not included in certificate's CN
```
**Causa:** Asterisk/PJSIP pone la IP en headers Via/Contact
**Solucion:** Kamailio como proxy TLS que reescribe headers con FQDN

### Problema 2: Certificado ECDSA no compatible
**Sintoma:** `TLS accept:error:0A0000C1:SSL routines::no shared cipher`
**Causa:** Let's Encrypt genera ECDSA por defecto, Microsoft requiere RSA
**Solucion:** Regenerar certificado con `--key-type rsa`

### Problema 3: Cipher suites no compatibles
**Sintoma:** `no shared cipher` incluso con certificado RSA
**Causa:** Kamailio no ofrecia los ciphers que Microsoft requiere
**Solucion:** Configurar cipher_list explicitamente:
```
ECDHE+AESGCM:DHE+AESGCM:ECDHE+AES:DHE+AES:AES256-GCM-SHA384:AES128-GCM-SHA256:HIGH:!aNULL:!MD5:!3DES
```

### Problema 4: SBC en status "Unknown"
**Sintoma:** Azure Portal mostraba SBC como Unknown
**Causa:** Microsoft necesita recibir OPTIONS periodicos (heartbeat)
**Solucion:** Cron job que envia OPTIONS cada minuto

---

## Configuracion Actual de Kamailio

Archivo: `/etc/kamailio/kamailio.cfg`

```kamailio
#!KAMAILIO

####### Global Parameters #########
debug=2
log_stderror=no
memdbg=5
memlog=5
children=4
auto_aliases=no
enable_tls=yes

listen=tls:0.0.0.0:5061

#!define FREEPBX_IP "172.18.0.2"
#!define FREEPBX_PORT 5060

####### Modules Section ########
loadmodule "tm.so"
loadmodule "sl.so"
loadmodule "rr.so"
loadmodule "pv.so"
loadmodule "textops.so"
loadmodule "siputils.so"
loadmodule "xlog.so"
loadmodule "sanity.so"
loadmodule "tls.so"

# ----- tls params -----
modparam("tls", "tls_method", "TLSv1.2")
modparam("tls", "certificate", "/etc/kamailio/certs/fullchain.pem")
modparam("tls", "private_key", "/etc/kamailio/certs/privkey.pem")
modparam("tls", "verify_certificate", 0)
modparam("tls", "require_certificate", 0)
modparam("tls", "cipher_list", "ECDHE+AESGCM:DHE+AESGCM:ECDHE+AES:DHE+AES:AES256-GCM-SHA384:AES128-GCM-SHA256:HIGH:!aNULL:!MD5:!3DES")
modparam("tls", "tls_force_run", 1)

# ----- rr params -----
modparam("rr", "enable_full_lr", 1)
modparam("rr", "append_fromtag", 1)

####### Routing Logic ########
request_route {
    xlog("L_INFO", "Received $rm from $si:$sp\n");

    if (!sanity_check()) {
        exit;
    }

    # Handle OPTIONS - respond with FQDN
    if (is_method("OPTIONS")) {
        append_hf("Contact: <sip:sbc.adrianpabonmendoza.com:5061;transport=tls>\r\n");
        sl_send_reply("200", "OK");
        exit;
    }

    if (!is_method("REGISTER")) {
        record_route();
    }

    if (has_totag()) {
        if (loose_route()) {
            route(RELAY);
        }
        exit;
    }

    route(RELAY);
}

route[RELAY] {
    $du = "sip:" + FREEPBX_IP + ":" + FREEPBX_PORT;
    xlog("L_INFO", "Forwarding to $du\n");

    if (!t_relay()) {
        sl_reply_error();
    }
    exit;
}

onreply_route {
    xlog("L_INFO", "Reply: $rs $rr\n");
}
```

---

## Heartbeat (Cron Job)

Script: `/usr/local/bin/send-options-microsoft.sh`
Cron: `/etc/cron.d/sbc-heartbeat`

```bash
# Cada minuto envia OPTIONS a Microsoft
* * * * * root /usr/local/bin/send-options-microsoft.sh
```

Log: `/var/log/sbc-heartbeat.log`

---

## Lecciones Aprendidas para Cisco CUBE

| Requisito | PoC (FreePBX/Kamailio) | Cisco CUBE Real |
|-----------|------------------------|-----------------|
| Certificado | RSA de Let's Encrypt | RSA de CA publica (DigiCert, GlobalSign) |
| Cipher TLS 1.2 | Configurar manualmente | Soportado nativo en IOS XE 16.11+ |
| Version IOS XE | N/A | Requiere 16.11+ (cliente tiene 16.09.01) |
| Headers FQDN | Kamailio reescribe | CUBE lo hace nativo con config correcta |

**IMPORTANTE:** El cliente debe:
1. Actualizar CUBE a IOS XE 16.11+ (o verificar que 16.09.01 soporte los ciphers)
2. Obtener certificado RSA de CA publica
3. Configurar los cipher suites correctos

---

## Comandos Utiles

### Verificar Kamailio
```bash
# Estado
sudo systemctl status kamailio

# Logs en tiempo real
sudo journalctl -u kamailio -f

# Reiniciar
sudo systemctl restart kamailio

# Verificar TLS y cipher
echo | openssl s_client -connect localhost:5061 -tls1_2 2>&1 | grep -i "cipher"

# Verificar certificado
echo | openssl s_client -connect sbc.adrianpabonmendoza.com:5061 2>/dev/null | openssl x509 -noout -subject -issuer
```

### Heartbeat
```bash
# Ver logs de heartbeat
sudo tail -f /var/log/sbc-heartbeat.log

# Ejecutar manualmente
sudo /usr/local/bin/send-options-microsoft.sh
```

### FreePBX
```bash
cd ~/optinoc-bocc-realtime/poc-sbc-simulado
docker compose ps
docker compose logs -f
docker exec -it freepbx-sbc asterisk -rvvv
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
- **Status: ONLINE**

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

## Proximos Pasos

1. **Configurar trunk en FreePBX** para recibir llamadas de Microsoft
2. **Probar llamada entrante** desde ACS → Kamailio → FreePBX
3. **Probar llamada saliente** FreePBX → Kamailio → ACS
4. **Integrar con API Python** para el flujo completo del voicebot

---

## Archivos Importantes en EC2

| Archivo | Descripcion |
|---------|-------------|
| `/etc/kamailio/kamailio.cfg` | Configuracion principal Kamailio |
| `/etc/kamailio/certs/` | Certificados Let's Encrypt (RSA) |
| `/usr/local/bin/send-options-microsoft.sh` | Script heartbeat |
| `/etc/cron.d/sbc-heartbeat` | Cron para heartbeat |
| `/var/log/sbc-heartbeat.log` | Log de heartbeats |
| `~/optinoc-bocc-realtime/poc-sbc-simulado/` | Directorio del PoC |

---

*Documento actualizado: 2026-02-03 02:00 UTC*
