# Estado del PoC - SBC Simulado con Azure ACS Direct Routing

> **Ultima actualizacion:** 2026-02-04 02:45 UTC
> **Estado:** SEÑALIZACION OK - AUDIO PENDIENTE (RTPEngine instalado)

---

## Resumen Ejecutivo

| Componente | Estado | Notas |
|------------|--------|-------|
| SBC Online en Azure | OK | EC2: 35.171.83.237 |
| TLS hacia Microsoft | OK | Intermitente - a veces falla |
| Señalizacion ACS → FreePBX | OK | INVITE, 183, 200 OK, ACK |
| Bridge FreePBX → Twilio | OK | Autenticacion funcionando |
| Llamada llega al telefono | **OK** | Usuario recibe la llamada |
| **Audio bidireccional** | **PENDIENTE** | Problema identificado: ICE/puertos |
| Llamadas entrantes (Twilio → ACS) | OK | Security Group corregido |
| RTPEngine instalado | OK | Pendiente configurar en Kamailio |

---

## Problema Actual: Audio

### Diagnostico (Sesion 2026-02-04)

El audio NO fluye correctamente. Los stats de Asterisk muestran:

```
kamailio:     Receive 0,   Transmit 602   ← No recibe de ACS, si envia
twilio-trunk: Receive 362, Transmit 0     ← Recibe de Twilio, no envia
```

**Causa raiz identificada:**
- FreePBX anuncia puerto X en SDP (ej: 10010)
- Pero ACS envia RTP a puerto Y diferente (ej: 10003)
- Esto ocurre porque ACS usa **ICE** y FreePBX no responde correctamente con candidatos ICE

### Lo que se intento:

1. **Habilitar ICE en FreePBX** → La llamada cuelga inmediatamente
2. **Deshabilitar ICE** → La llamada se mantiene pero sin audio
3. **Configurar STUN** → No resolvio el problema
4. **Ajustar rango RTP** → Puertos 10000-10100 correctamente mapeados en Docker
5. **Instalar RTPEngine** → Instalado pero no configurado completamente

### Conclusion:
FreePBX no maneja ICE correctamente con Microsoft ACS. La solucion es usar **RTPEngine** como media proxy.

---

## RTPEngine - Estado de Instalacion

RTPEngine esta instalado y corriendo:

```bash
# Verificar estado
sudo systemctl status rtpengine-daemon

# Configuracion actual
cat /etc/rtpengine/rtpengine.conf
```

**Configuracion actual:**
```ini
[rtpengine]
interface = internal/127.0.0.1;external/35.171.83.237
listen-ng = 127.0.0.1:2223
port-min = 20000
port-max = 20100
timeout = 60
silent-timeout = 600
delete-delay = 30
```

**Puertos abiertos en AWS Security Group:**
- 20000-20100 UDP (para RTPEngine)
- 10000-10100 UDP (para FreePBX)
- 1024-65535 UDP (para RTP de Microsoft)
- 5060 UDP (SIP Twilio)
- 5061 TCP (TLS Microsoft)

---

## Proximos Pasos para Resolver Audio

### Paso 1: Configurar Kamailio con RTPEngine

Modificar `/etc/kamailio/kamailio.cfg` para usar RTPEngine:

```kamailio
# Agregar modulo
loadmodule "rtpengine.so"
modparam("rtpengine", "rtpengine_sock", "udp:127.0.0.1:2223")

# En request_route, para INVITE:
if (is_method("INVITE") && has_body("application/sdp")) {
    rtpengine_manage("replace-origin replace-session-connection ICE=remove RTP/AVP");
}

# En onreply_route:
if (has_body("application/sdp")) {
    rtpengine_manage("replace-origin replace-session-connection ICE=remove RTP/AVP");
}
```

### Paso 2: Probar con RTPEngine

```bash
# Reiniciar Kamailio
sudo systemctl restart kamailio

# Hacer llamada de prueba
python3 ~/test_call.py

# Verificar sesiones RTPEngine
# (no hay comando ctl en esta version, ver logs)
sudo journalctl -u rtpengine-daemon -f
```

### Paso 3: Si RTPEngine no funciona

Opciones alternativas:
1. Usar **Onesip** o **AudioCodes Live** (SBC en la nube certificado)
2. Ir directo a probar con **Cisco CUBE** del cliente (ya certificado por Microsoft)

---

## Arquitectura con RTPEngine

```
Azure ACS                RTPEngine               FreePBX              Twilio
    │                        │                       │                    │
    │◄──SRTP/ICE────────────►│◄──────RTP────────────►│◄───────RTP────────►│
    │   (puerto 20000+)      │   (interno)           │   (puerto 10000+)  │
    │                        │                       │                    │
    └────────────────────────┴───────────────────────┴────────────────────┘
                             │
                    RTPEngine maneja:
                    - SRTP ↔ RTP conversion
                    - ICE negotiation
                    - NAT traversal
```

---

## Configuracion Actual de Componentes

### Kamailio (/etc/kamailio/kamailio.cfg)
```
listen=tls:0.0.0.0:5061 advertise sbc.adrianpabonmendoza.com:5061
listen=udp:0.0.0.0:5062 advertise sbc.adrianpabonmendoza.com:5062
modparam("tls", "cipher_list", "ECDHE-RSA-AES256-GCM-SHA384:...")
# RTPEngine NO configurado aun
```

### FreePBX - Endpoint Kamailio (/etc/asterisk/pjsip_custom.conf)
```ini
[kamailio]
type=endpoint
context=from-trunk-custom
disallow=all
allow=ulaw
allow=alaw
direct_media=no
rtp_symmetric=yes
force_rport=yes
rewrite_contact=yes
media_encryption=sdes
media_encryption_optimistic=yes
ice_support=no
```

### FreePBX - RTP (/etc/asterisk/rtp_additional.conf)
```ini
[general]
rtpstart=10000
rtpend=10100
strictrtp=no
```

---

## Comandos Utiles

```bash
# Conectar a EC2
ssh -i ~/opti-freepbx.pem ubuntu@35.171.83.237

# === Kamailio ===
sudo systemctl status kamailio
sudo journalctl -u kamailio -f
sudo kamailio -c  # Verificar config

# === RTPEngine ===
sudo systemctl status rtpengine-daemon
sudo journalctl -u rtpengine-daemon -f
cat /etc/rtpengine/rtpengine.conf

# === FreePBX/Asterisk ===
docker exec freepbx-sbc asterisk -rx "core show channels"
docker exec freepbx-sbc asterisk -rx "pjsip show channelstats"
docker exec freepbx-sbc asterisk -rx "pjsip show endpoint kamailio"
docker exec freepbx-sbc tail -f /var/log/asterisk/full

# === Probar llamada ===
python3 ~/test_call.py

# === Capturar trafico ===
sudo tcpdump -i any port 5061 -w /tmp/sip.pcap
sudo tcpdump -i any udp portrange 10000-20100 -c 50
```

---

## Problemas Resueltos en Sesiones Anteriores

1. **Endpoint kamailio no cargaba** → Mover a pjsip_custom.conf
2. **488 Not Acceptable** → Habilitar SRTP (media_encryption=sdes)
3. **Record-Route 0.0.0.0** → Agregar advertise en Kamailio
4. **403 Forbidden** → Cambiar contexto a from-trunk-custom
5. **407 Auth Required** → Agregar realm=sip.twilio.com
6. **Error 32011 Twilio** → Abrir puertos en AWS Security Group
7. **Error 32204 Twilio** → Abrir puerto 5060 UDP para IPs de Twilio
8. **Puertos RTP fuera de rango Docker** → Ajustar rtpend=10100

---

## Problemas Conocidos

1. **TLS intermitente**: A veces Kamailio reporta "no shared cipher" al reiniciar. Se resuelve solo despues de unos minutos.

2. **ICE con FreePBX**: FreePBX/Asterisk no maneja ICE correctamente con Microsoft ACS. Solucion: RTPEngine.

---

## Credenciales

| Servicio | Credencial |
|----------|------------|
| EC2 SSH | `ssh -i ~/opti-freepbx.pem ubuntu@35.171.83.237` |
| Twilio User | freepbx-user |
| Twilio Pass | Opting0c2026! |
| Twilio Trunk | optinoc-poc.pstn.twilio.com |
| Numero Twilio | +14846736495 |
| SBC FQDN | sbc.adrianpabonmendoza.com:5061 |

---

## Nota sobre Cisco CUBE

El problema de audio es especifico de FreePBX. **Cisco CUBE** (el SBC real del cliente) esta certificado por Microsoft para Direct Routing y deberia manejar ICE/SRTP correctamente sin estos problemas.

Si RTPEngine no resuelve el problema, la recomendacion es:
1. Probar directamente con Cisco CUBE del cliente
2. O usar un SBC en la nube certificado (AudioCodes, Onesip)

---

*Documento actualizado: 2026-02-04 02:45 UTC*
