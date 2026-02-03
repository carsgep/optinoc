# Guia de Instalacion - SBC para Azure ACS Direct Routing

> **Version:** 1.0
> **Probado en:** Ubuntu 24.04 (EC2 AWS)
> **Aplicable a:** Azure VM, AWS EC2, cualquier VM con Ubuntu

---

## Prerequisitos

### 1. VM/Servidor
- Ubuntu 22.04 o 24.04
- Minimo 2 vCPU, 2GB RAM
- IP publica estatica

### 2. DNS
- Un dominio con acceso a configurar DNS
- Registro A apuntando a la IP publica de la VM
- Ejemplo: `sbc.tudominio.com` → `IP_PUBLICA`

### 3. Puertos de Firewall/Security Group

| Puerto | Protocolo | Origen | Uso |
|--------|-----------|--------|-----|
| 22 | TCP | Tu IP | SSH |
| 80 | TCP | 0.0.0.0/0 | Let's Encrypt |
| 5060 | TCP/UDP | 0.0.0.0/0 | SIP (Twilio/PSTN) |
| 5061 | TCP | 52.112.0.0/14, 52.120.0.0/14 | SIP TLS (Microsoft) |
| 10000-20000 | UDP | 0.0.0.0/0 | RTP Audio |

---

## Paso 1: Preparar el Servidor

```bash
# Conectar por SSH
ssh -i tu-llave.pem ubuntu@IP_PUBLICA

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias basicas
sudo apt install -y git docker.io docker-compose-v2 certbot
```

---

## Paso 2: Obtener Certificado RSA

**IMPORTANTE:** El certificado DEBE ser RSA, no ECDSA. Microsoft no acepta ECDSA.

```bash
# Obtener certificado Let's Encrypt con llave RSA
sudo certbot certonly --standalone \
    -d sbc.tudominio.com \
    --non-interactive \
    --agree-tos \
    --email tu@email.com \
    --key-type rsa \
    --rsa-key-size 2048

# Verificar que es RSA
sudo openssl x509 -in /etc/letsencrypt/live/sbc.tudominio.com/fullchain.pem -noout -text | grep "Public Key Algorithm"
# Debe mostrar: rsaEncryption
```

---

## Paso 3: Instalar Kamailio

```bash
# Instalar Kamailio
sudo apt install -y kamailio kamailio-tls-modules

# Crear directorio para certificados
sudo mkdir -p /etc/kamailio/certs

# Copiar certificados
sudo cp /etc/letsencrypt/live/sbc.tudominio.com/fullchain.pem /etc/kamailio/certs/
sudo cp /etc/letsencrypt/live/sbc.tudominio.com/privkey.pem /etc/kamailio/certs/
sudo chown -R kamailio:kamailio /etc/kamailio/certs/
```

---

## Paso 4: Configurar Kamailio

Crear archivo `/etc/kamailio/kamailio.cfg`:

```bash
sudo tee /etc/kamailio/kamailio.cfg > /dev/null << 'EOF'
#!KAMAILIO

####### Global Parameters #########
debug=2
log_stderror=no
memdbg=5
memlog=5
children=4
auto_aliases=no
enable_tls=yes

# CAMBIAR: Tu FQDN aqui
listen=tls:0.0.0.0:5061

# CAMBIAR: IP de tu FreePBX/PBX interno
#!define PBX_IP "172.18.0.2"
#!define PBX_PORT 5060

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

# ----- TLS params (CRITICO para Microsoft) -----
modparam("tls", "tls_method", "TLSv1.2")
modparam("tls", "certificate", "/etc/kamailio/certs/fullchain.pem")
modparam("tls", "private_key", "/etc/kamailio/certs/privkey.pem")
modparam("tls", "verify_certificate", 0)
modparam("tls", "require_certificate", 0)
# Cipher suites requeridos por Microsoft
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

    # Handle OPTIONS - respond with FQDN (CAMBIAR sbc.tudominio.com)
    if (is_method("OPTIONS")) {
        append_hf("Contact: <sip:sbc.tudominio.com:5061;transport=tls>\r\n");
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
    $du = "sip:" + PBX_IP + ":" + PBX_PORT;
    xlog("L_INFO", "Forwarding to $du\n");

    if (!t_relay()) {
        sl_reply_error();
    }
    exit;
}

onreply_route {
    xlog("L_INFO", "Reply: $rs $rr\n");
}
EOF
```

**Reiniciar Kamailio:**

```bash
sudo systemctl enable kamailio
sudo systemctl restart kamailio
sudo systemctl status kamailio
```

---

## Paso 5: Configurar Heartbeat a Microsoft

Microsoft requiere que el SBC envie OPTIONS periodicamente.

**Crear script** `/usr/local/bin/send-options-microsoft.sh`:

```bash
sudo tee /usr/local/bin/send-options-microsoft.sh > /dev/null << 'EOF'
#!/bin/bash
# CAMBIAR: Tu FQDN
FQDN="sbc.tudominio.com"
MICROSOFT_HOST="sip.pstnhub.microsoft.com"
CERT="/etc/kamailio/certs/fullchain.pem"
KEY="/etc/kamailio/certs/privkey.pem"
BRANCH="z9hG4bK$(date +%s)"
CALLID="options-$(date +%s)@${FQDN}"

OPTIONS_MSG="OPTIONS sip:${MICROSOFT_HOST}:5061 SIP/2.0\r
Via: SIP/2.0/TLS ${FQDN}:5061;branch=${BRANCH}\r
From: <sip:${FQDN}>;tag=heartbeat\r
To: <sip:${MICROSOFT_HOST}>\r
Call-ID: ${CALLID}\r
CSeq: 1 OPTIONS\r
Contact: <sip:${FQDN}:5061;transport=tls>\r
Max-Forwards: 70\r
User-Agent: Kamailio-SBC/1.0\r
Content-Length: 0\r
\r
"

RESPONSE=$(echo -e "$OPTIONS_MSG" | timeout 10 openssl s_client \
    -connect ${MICROSOFT_HOST}:5061 \
    -cert ${CERT} \
    -key ${KEY} \
    -quiet 2>/dev/null | head -1)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
if [[ "$RESPONSE" == *"200"* ]]; then
    echo "${TIMESTAMP} - OPTIONS OK: $RESPONSE" >> /var/log/sbc-heartbeat.log
else
    echo "${TIMESTAMP} - OPTIONS FAILED: $RESPONSE" >> /var/log/sbc-heartbeat.log
fi
EOF

sudo chmod +x /usr/local/bin/send-options-microsoft.sh
```

**Configurar cron:**

```bash
echo "* * * * * root /usr/local/bin/send-options-microsoft.sh" | sudo tee /etc/cron.d/sbc-heartbeat
sudo systemctl restart cron
```

**Probar manualmente:**

```bash
sudo /usr/local/bin/send-options-microsoft.sh
cat /var/log/sbc-heartbeat.log
# Debe mostrar: OPTIONS OK: SIP/2.0 200 OK
```

---

## Paso 6: Configurar Azure ACS

1. Ir a **Azure Portal** → **Communication Services** → tu recurso
2. **Direct Routing** → **Session Border Controllers** → **Add**
3. Configurar:
   - FQDN: `sbc.tudominio.com`
   - Puerto: `5061`
4. Click **Add**
5. Esperar 2-5 minutos hasta que **Status = Online**

6. **Voice Routes** → **Add**:
   - Name: `Colombia-Route` (o el nombre que quieras)
   - Number Pattern: `^\+57(\d+)$` (para Colombia)
   - SBC: `sbc.tudominio.com`
   - Priority: 1

---

## Paso 7: Verificar Funcionamiento

```bash
# Verificar Kamailio
sudo systemctl status kamailio

# Verificar TLS y cipher
echo | openssl s_client -connect localhost:5061 -tls1_2 2>&1 | grep -i "cipher"
# Debe mostrar: ECDHE-RSA-AES256-GCM-SHA384

# Verificar heartbeat
tail -5 /var/log/sbc-heartbeat.log
# Debe mostrar: OPTIONS OK

# Verificar logs de Kamailio
sudo journalctl -u kamailio -f
```

---

## Troubleshooting

### Error: "no shared cipher"
**Causa:** Certificado ECDSA en lugar de RSA
**Solucion:**
```bash
sudo certbot certonly --standalone \
    -d sbc.tudominio.com \
    --cert-name sbc.tudominio.com \
    --key-type rsa \
    --rsa-key-size 2048 \
    --force-renewal

# Copiar nuevos certificados
sudo cp /etc/letsencrypt/live/sbc.tudominio.com/*.pem /etc/kamailio/certs/
sudo chown -R kamailio:kamailio /etc/kamailio/certs/
sudo systemctl restart kamailio
```

### Error: SBC en status "Unknown" en Azure
**Causa:** Microsoft no recibe heartbeat
**Solucion:**
1. Verificar que el cron esta corriendo: `cat /etc/cron.d/sbc-heartbeat`
2. Probar manualmente: `sudo /usr/local/bin/send-options-microsoft.sh`
3. Ver log: `cat /var/log/sbc-heartbeat.log`

### Error: "403 Forbidden" de Microsoft
**Causa:** FQDN no coincide con certificado
**Solucion:** Verificar que el FQDN en Kamailio y en el certificado sean identicos

---

## Migracion de EC2 a Azure VM

Si ya tienes esto funcionando en EC2 y quieres mover a Azure:

1. **Crear VM en Azure** con Ubuntu 24.04
2. **Asignar IP publica estatica**
3. **Actualizar DNS** en Cloudflare para apuntar a nueva IP
4. **Esperar propagacion DNS** (puede tomar hasta 1 hora)
5. **Seguir esta guia desde Paso 1** en la nueva VM
6. **Verificar en Azure Portal** que SBC muestre "Online"

**Nota:** No necesitas eliminar el SBC de Azure, solo cambiar el DNS.

---

## Archivos de Referencia

| Archivo | Descripcion |
|---------|-------------|
| `/etc/kamailio/kamailio.cfg` | Configuracion principal |
| `/etc/kamailio/certs/` | Certificados TLS |
| `/usr/local/bin/send-options-microsoft.sh` | Script heartbeat |
| `/etc/cron.d/sbc-heartbeat` | Cron para heartbeat |
| `/var/log/sbc-heartbeat.log` | Log de heartbeats |

---

*Guia creada: 2026-02-03*
