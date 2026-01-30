# Cuestionario Tecnico - Cisco CUBE
## Informacion requerida para implementacion Direct Routing con Azure ACS

**Para:** Equipo de Redes/Telefonia - Banco de Occidente
**De:** Optimize IT
**Fecha:** Enero 2026
**Proyecto:** Optinoc VoiceBot - Integracion Direct Routing

---

## Informacion Ya Conocida

| Componente | Valor | Administrador |
|------------|-------|---------------|
| Cisco Unified CM | 12.5.1.13900-152 | Proveedor de telefonia |
| Cisco CUBE | IOS XE 16.09.01 (Fuji) | Banco de Occidente |
| Plataforma CUBE | ASR1000 | Banco de Occidente |

---

## ALERTA: Version de IOS XE

La version actual del CUBE es **IOS XE 16.09.01**.

Microsoft recomienda **IOS XE 16.11 o superior** para soporte completo de TLS 1.2 con los cipher suites requeridos.

**Pregunta critica:**
- Es posible actualizar el CUBE a IOS XE 16.11 o superior?
- Si no es posible, que cipher suites TLS 1.2 soporta la version 16.09.01?

---

## Seccion 1: Conectividad del CUBE

### 1.1 Direccionamiento IP

| Pregunta | Respuesta |
|----------|-----------|
| El CUBE tiene IP publica directa? | [ ] Si / [ ] No |
| Si tiene IP publica, cual es? | _________________ |
| Esta detras de NAT? | [ ] Si / [ ] No |
| IP privada del CUBE (si aplica) | _________________ |

### 1.2 FQDN (Nombre de Dominio)

| Pregunta | Respuesta |
|----------|-----------|
| El CUBE tiene un FQDN publico actualmente? | [ ] Si / [ ] No |
| Si lo tiene, cual es? | _________________ |
| Si no lo tiene, pueden crear uno? | [ ] Si / [ ] No |
| Dominio sugerido (ej: sbc.bancooccidente.com) | _________________ |

**Nota:** Azure ACS requiere que el CUBE tenga un FQDN publico resoluble desde internet.

---

## Seccion 2: Certificados TLS

### 2.1 Estado Actual

| Pregunta | Respuesta |
|----------|-----------|
| El CUBE tiene certificado TLS instalado actualmente? | [ ] Si / [ ] No |
| Si lo tiene, quien lo emitio? | [ ] CA Publica / [ ] CA Corporativa / [ ] Autofirmado |
| Nombre de la CA (si es publica) | _________________ |
| Fecha de vencimiento del certificado | _________________ |

### 2.2 Si No Tiene Certificado de CA Publica

| Pregunta | Respuesta |
|----------|-----------|
| Pueden adquirir un certificado de CA publica? | [ ] Si / [ ] No |
| (DigiCert, GlobalSign, Sectigo, Let's Encrypt) | |
| Quien aprobaria la compra? | _________________ |
| Tiempo estimado para adquirirlo | _________________ |

**Requisito Azure:** El certificado DEBE ser de una CA publica reconocida por Microsoft. NO se aceptan certificados autofirmados ni de CA corporativa interna.

---

## Seccion 3: Configuracion Actual del CUBE

### 3.1 TLS

| Pregunta | Respuesta |
|----------|-----------|
| TLS esta habilitado en el CUBE? | [ ] Si / [ ] No |
| Version de TLS configurada | [ ] 1.0 / [ ] 1.1 / [ ] 1.2 |
| Cipher suites configurados | _________________ |

**Requerido por Azure:**
- TLS 1.2 obligatorio
- Cipher suites: `TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384` o `TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`

### 3.2 SRTP

| Pregunta | Respuesta |
|----------|-----------|
| SRTP esta habilitado en el CUBE? | [ ] Si / [ ] No |
| Cifrado configurado | _________________ |

**Requerido por Azure:** Cifrado `AES_CM_128_HMAC_SHA1_80`

### 3.3 Codecs

| Pregunta | Respuesta |
|----------|-----------|
| Codecs habilitados actualmente | [ ] G.711 u-law |
| | [ ] G.711 A-law |
| | [ ] G.722 |
| | [ ] G.729 |
| | [ ] Otros: _________ |

---

## Seccion 4: Firewall y Red

### 4.1 Acceso Entrante

| Pregunta | Respuesta |
|----------|-----------|
| Pueden abrir puertos entrantes desde internet? | [ ] Si / [ ] No |
| Quien autoriza cambios de firewall? | _________________ |
| Tiempo estimado para aprobar reglas | _________________ |

**Reglas requeridas (entrantes hacia el CUBE):**

```
PERMITIR TCP 5061       DESDE 52.112.0.0/14, 52.120.0.0/14
PERMITIR UDP 49152-53247 DESDE 52.112.0.0/14, 52.120.0.0/14
```

### 4.2 Acceso Saliente

| Pregunta | Respuesta |
|----------|-----------|
| El CUBE puede hacer conexiones salientes a internet? | [ ] Si / [ ] No |
| Hay restricciones de salida? | _________________ |

**Destinos salientes requeridos:**
- `sip.pstnhub.microsoft.com:5061`
- `sip2.pstnhub.microsoft.com:5061`
- `sip3.pstnhub.microsoft.com:5061`

---

## Seccion 5: Dial-peers y Enrutamiento

### 5.1 Configuracion de Dial-peers

| Pregunta | Respuesta |
|----------|-----------|
| Pueden agregar nuevos dial-peers en el CUBE? | [ ] Si / [ ] No |
| Hay dial-peers existentes hacia Microsoft/Teams? | [ ] Si / [ ] No |
| Quien realiza cambios en el CUBE? | _________________ |

### 5.2 Numeros Telefonicos

| Pregunta | Respuesta |
|----------|-----------|
| Numero telefonico disponible para asignar al bot | _________________ |
| (Formato E.164, ej: +576012345678) | |
| Este numero esta asociado al CUBE actualmente? | [ ] Si / [ ] No |

---

## Seccion 6: Disponibilidad y Mantenimiento

| Pregunta | Respuesta |
|----------|-----------|
| Ventana de mantenimiento disponible | _________________ |
| Hay ambiente de pruebas/staging? | [ ] Si / [ ] No |
| Contacto tecnico principal | _________________ |
| Telefono/Email de contacto | _________________ |

---

## Seccion 7: Integracion con CUCM

| Pregunta | Respuesta |
|----------|-----------|
| El CUBE tiene trunk hacia el CUCM actualmente? | [ ] Si / [ ] No |
| Protocolo del trunk (SIP/H.323) | _________________ |
| El proveedor de telefonia debe involucrarse? | [ ] Si / [ ] No |

---

## Resumen de Acciones Requeridas del Banco

Basado en los requerimientos de Azure ACS Direct Routing:

### Obligatorias

- [ ] Proveer FQDN publico para el CUBE
- [ ] Instalar certificado TLS de CA publica
- [ ] Habilitar TLS 1.2 con cipher suites compatibles
- [ ] Habilitar SRTP con cifrado AES
- [ ] Abrir puertos de firewall para IPs de Microsoft
- [ ] Configurar dial-peers hacia Microsoft
- [ ] Asignar numero telefonico para el bot

### Potencialmente Requeridas

- [ ] Actualizar IOS XE de 16.09.01 a 16.11+ (si TLS 1.2 no funciona correctamente)
- [ ] Coordinar con proveedor de telefonia (si afecta CUCM)

---

## Proximos Pasos

1. **Banco completa este cuestionario** con la informacion tecnica
2. **Optimize IT revisa** las respuestas y valida compatibilidad
3. **Reunion tecnica** para definir plan de implementacion
4. **Prueba de concepto** en ambiente controlado
5. **Implementacion** en produccion

---

## Contacto Optimize IT

Para consultas sobre este cuestionario:
- **Proyecto:** Optinoc VoiceBot
- **Email:** [tu email]
- **Telefono:** [tu telefono]

---

*Documento generado: Enero 2026*
