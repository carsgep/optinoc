# Integración Direct Routing: Azure Communication Services + Cisco CUBE

## Contexto Colombia

- **No es posible comprar números telefónicos de Azure en Colombia**
- La única opción para llamadas PSTN es **Direct Routing**
- Se utiliza la infraestructura telefónica existente del cliente (Cisco CUBE)

---

## 1. Lo que el Cliente debe Proveer

| Dato | Ejemplo | Uso |
|------|---------|-----|
| **FQDN del CUBE** | `sbc.bancooccidente.com` | Registrar en ACS como SBC |
| **Puerto SIP** | `5061` | Configurar en ACS |
| **Número telefónico** | `+576012345678` | Caller ID para llamadas salientes |

### Requisitos del FQDN

- Debe ser **público** (resoluble desde internet)
- Debe tener un registro DNS tipo A apuntando a la IP pública del CUBE
- Ejemplo: `sbc.bancooccidente.com → 200.X.X.X`

---

## 2. Configuración de Firewall del Cliente

El cliente debe permitir tráfico **entrante** desde las IPs de Microsoft Azure.

### Rangos de IP de Microsoft ACS

| Rango CIDR | Rango Expandido |
|------------|-----------------|
| `52.112.0.0/14` | 52.112.0.0 - 52.115.255.255 |
| `52.120.0.0/14` | 52.120.0.0 - 52.123.255.255 |

### Puertos a Abrir

| Protocolo | Puerto | Dirección | Propósito |
|-----------|--------|-----------|-----------|
| TCP | 5061 | Entrante | SIP señalización (TLS) |
| UDP | 49152-53247 | Entrante | Media (RTP/SRTP) |

### Regla de Firewall Resumida

```
PERMITIR TCP 5061       DESDE 52.112.0.0/14, 52.120.0.0/14
PERMITIR UDP 49152-53247 DESDE 52.112.0.0/14, 52.120.0.0/14
```

---

## 3. Configuración del CUBE (Lado Cliente)

El cliente debe configurar en su Cisco CUBE:

### 3.1 Certificado TLS

| Requisito | Especificación |
|-----------|----------------|
| Tipo | CA pública (DigiCert, GlobalSign, Sectigo, etc.) |
| NO autofirmado | Microsoft no acepta certificados autofirmados |
| CN o SAN | Debe incluir el FQDN del CUBE |
| Key size | Mínimo 2048 bits |
| EKU | Server Authentication |

### 3.2 Protocolo TLS

- **Versión:** TLS 1.2 (obligatorio)
- **Cipher suites soportados:**
  - `TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384`
  - `TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`
  - `TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA384`
  - `TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256`

### 3.3 SRTP

- **Cifrado:** `AES_CM_128_HMAC_SHA1_80` (obligatorio)

### 3.4 Códecs Soportados

- G.711 μ-law
- G.711 A-law
- G.722
- SILK
- G.729

### 3.5 Dial Peer hacia Microsoft

El CUBE debe tener dial-peers configurados hacia los FQDNs de Microsoft:

| FQDN | Prioridad |
|------|-----------|
| `sip.pstnhub.microsoft.com` | 1 (primario) |
| `sip2.pstnhub.microsoft.com` | 2 (failover) |
| `sip3.pstnhub.microsoft.com` | 3 (failover) |

---

## 4. Glosario: ¿Qué es TLS, SRTP y Dial-peers?

### TLS (Transport Layer Security)

**Qué es:** Cifrado para la señalización SIP.

**Analogía:** Es como HTTPS pero para llamadas. Protege los mensajes de "llamar", "colgar", "transferir", etc.

```
Sin TLS:  CUBE ──── SIP en texto plano ────> Microsoft  ❌ Rechazado
Con TLS:  CUBE ──── SIP cifrado (TLS) ─────> Microsoft  ✅ Aceptado
```

**Requisito:** TLS 1.2 + certificado de CA pública

---

### SRTP (Secure Real-time Transport Protocol)

**Qué es:** Cifrado para el audio de la llamada.

**Analogía:** TLS protege los comandos, SRTP protege la voz.

```
Sin SRTP:  Audio en claro ──────> Cualquiera puede escuchar  ❌
Con SRTP:  Audio cifrado ───────> Solo los participantes     ✅
```

**Requisito:** Cifrado `AES_CM_128_HMAC_SHA1_80`

---

### Dial-peers

**Qué es:** Reglas de enrutamiento de llamadas en el CUBE.

**Analogía:** Es como una tabla de rutas. "Si el destino es X, envía la llamada por Y".

```
Dial-peer 100:
  Si llega llamada DESDE Microsoft (sip.pstnhub.microsoft.com)
  → Enviarla a la red PSTN interna

Dial-peer 200:
  Si llega llamada HACIA Microsoft
  → Enviarla a sip.pstnhub.microsoft.com:5061
```

---

### Resumen Visual de Componentes del CUBE

```
┌─────────────────────────────────────────────────────────┐
│                      CISCO CUBE                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   TLS 1.2 + Certificado                                 │
│   └─> Cifra la señalización (SIP)                       │
│                                                         │
│   SRTP                                                  │
│   └─> Cifra el audio (voz)                              │
│                                                         │
│   Dial-peers                                            │
│   └─> Reglas: "llamadas de Microsoft van a PSTN"        │
│   └─> Reglas: "llamadas a Microsoft van por TLS:5061"   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### ¿Quién configura esto?

El **equipo de redes/telefonía del cliente**. Ellos conocen su CUBE.

Optinoc solo necesita que le den el FQDN, puerto y número cuando terminen.

---

## 5. Lo que Yo (Optinoc) debo Configurar

### 5.1 En Azure Communication Services

1. **Agregar el SBC del cliente**
   - FQDN: `sbc.bancooccidente.com` (el que provea el cliente)
   - Puerto: `5061`

2. **Configurar Voice Routes**
   - Patrón de números: `^\+57(\d+)$` (números Colombia)
   - Asociar al SBC del cliente

3. **Verificar estado "Online"**
   - Esperar ~15 minutos después de configurar
   - El SBC debe mostrar estado "Online" en Azure Portal

### 5.2 En la Aplicación (main.py)

Agregar la variable de entorno con el número del cliente:

```bash
# .env
ACS_PHONE_NUMBER=+576012345678  # Número que provee el cliente
```

Modificar el código para incluir `source_caller_id_number` en llamadas PSTN.

### 5.3 Variables de Entorno Requeridas

```bash
# Obligatorias
ACS_CONNECTION_STRING=endpoint=https://xxx.communication.azure.com/;accesskey=xxx
CALLBACK_URI=https://tu-url-publica.com
OPENAI_API_KEY=sk-xxx
ACS_PHONE_NUMBER=+576012345678  # Número del cliente para caller ID

# Opcional (para llamadas Teams en horario laboral)
TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

## 6. Flujo de una Llamada PSTN

```
1. App llama POST /calls/outbound
   └─> target_number: "+573001234567"

2. Azure Communication Services
   └─> Busca voice route para +57...
   └─> Encuentra SBC: sbc.bancooccidente.com

3. ACS → CUBE del cliente
   └─> SIP INVITE via TLS (puerto 5061)
   └─> Desde IPs: 52.112.x.x / 52.120.x.x

4. CUBE → Red PSTN del cliente
   └─> Enruta llamada al destino

5. Persona contesta
   └─> CallConnected event
   └─> Inicia media streaming bidireccional
   └─> OPTI (bot) comienza a hablar
```

---

## 7. Importante: Certificación de SBC

### Estado Actual

| SBC | Certificado para ACS |
|-----|---------------------|
| AudioCodes | ✅ Sí |
| Ribbon | ✅ Sí |
| Oracle | ✅ Sí |
| Metaswitch | ✅ Sí |
| TE-SYSTEMS | ✅ Sí |
| **Cisco CUBE** | ❌ **No certificado** |

### Implicaciones

- Cisco CUBE **no está oficialmente certificado** para ACS Direct Routing
- **Puede funcionar** porque ACS comparte backend con Teams Direct Routing (donde Cisco sí está certificado)
- Microsoft **no da soporte oficial** si hay problemas con Cisco CUBE
- Recomendación: Hacer prueba de concepto antes de producción

### Contacto para Certificación

Si el cliente quiere información sobre certificación:
- Email: `acsdrcertification@microsoft.com`

---

## 8. Referencias Oficiales

| Documento | URL |
|-----------|-----|
| Requisitos de Infraestructura | https://learn.microsoft.com/en-us/azure/communication-services/concepts/telephony/direct-routing-infrastructure |
| SBCs Certificados | https://learn.microsoft.com/en-us/azure/communication-services/concepts/telephony/certified-session-border-controllers |
| Provisioning Direct Routing | https://learn.microsoft.com/en-us/azure/communication-services/concepts/telephony/direct-routing-provisioning |
| IPs de Azure (JSON actualizado) | https://www.microsoft.com/en-us/download/details.aspx?id=56519 |

---

## 9. Checklist de Implementación

### Cliente debe completar:

- [ ] Proveer FQDN del CUBE
- [ ] Proveer puerto SIP (generalmente 5061)
- [ ] Proveer número telefónico para caller ID
- [ ] Instalar certificado TLS de CA pública en CUBE
- [ ] Configurar TLS 1.2 en CUBE
- [ ] Configurar SRTP en CUBE
- [ ] Abrir firewall para IPs de Microsoft (52.112.0.0/14, 52.120.0.0/14)
- [ ] Configurar dial-peers hacia Microsoft en CUBE

### Optinoc debe completar:

- [ ] Registrar SBC en Azure Communication Services
- [ ] Configurar voice routes en ACS
- [ ] Verificar estado "Online" del SBC
- [ ] Configurar variable ACS_PHONE_NUMBER en .env
- [ ] Modificar código para incluir source_caller_id_number
- [ ] Probar llamada de prueba

---

## 10. Preguntas Frecuentes del Cliente

**P: ¿Por qué no compran ustedes un número en Azure?**
R: Azure Communication Services no ofrece números telefónicos para Colombia. La única opción es Direct Routing usando la infraestructura existente del cliente.

**P: ¿Qué pasa si nuestro CUBE no está certificado?**
R: Cisco CUBE no está en la lista de SBCs certificados para ACS, pero puede funcionar porque comparte tecnología con Teams Direct Routing. Sin embargo, Microsoft no ofrece soporte oficial. Se recomienda hacer una prueba de concepto.

**P: ¿Qué certificado TLS necesitamos?**
R: Un certificado de una CA pública (no autofirmado). Puede ser DigiCert, GlobalSign, Sectigo, Let's Encrypt, etc. El CN debe coincidir con el FQDN del CUBE.

**P: ¿Pueden usar nuestro certificado interno/corporativo?**
R: No. Microsoft solo acepta certificados de CAs que estén en el Microsoft Trusted Root Certificate Program.

**P: ¿Cuánto tarda en activarse?**
R: Después de configurar el SBC en ACS, esperar aproximadamente 15 minutos para que el estado cambie a "Online".

**P: ¿Por qué el FQDN debe ser público?**
R: Porque Azure Communication Services está en la nube de Microsoft, no en la red del cliente. ACS necesita resolver el nombre DNS y conectarse al CUBE a través de internet.

**P: ¿Cuánto cuesta?**
R: ACS cobra ~$0.004/min por llamada. El costo PSTN depende del proveedor actual del cliente.

**P: ¿Necesitamos licencias adicionales?**
R: No de Microsoft. Solo verificar que el CUBE tenga licencia activa.

**P: ¿Qué pasa si el CUBE se cae?**
R: Las llamadas fallan. Se puede configurar un SBC secundario como failover.

**P: ¿Pueden grabar las llamadas?**
R: Sí, ACS soporta grabación (+$0.002/min).

**P: ¿Funciona con nuestro Call Manager (CUCM)?**
R: Sí. El CUBE se conecta al Call Manager, ACS se conecta al CUBE. No hay cambio en la arquitectura interna.

**P: ¿Cuántas llamadas simultáneas soporta?**
R: Depende de la capacidad del CUBE y el ancho de banda. ACS no tiene límite práctico.

**P: ¿Qué versión de IOS necesita el CUBE?**
R: IOS XE 16.11 o superior para soporte completo de TLS 1.2.

**P: ¿Quién da soporte si algo falla?**
R: Optinoc para la aplicación, el cliente para el CUBE, Microsoft para ACS. Nota: Cisco CUBE no tiene soporte oficial de Microsoft con ACS.

---

## 11. Pasos para Continuar con la Implementación

### Fase 1: Cliente prepara su infraestructura

1. Asignar FQDN público para el CUBE (ej: `sbc.banco.com`)
2. Comprar/instalar certificado TLS de CA pública
3. Abrir firewall para IPs de Microsoft
4. Configurar CUBE (TLS 1.2, SRTP, dial-peers)
5. Definir número telefónico para caller ID

### Fase 2: Optinoc configura Azure

1. Cliente envía: FQDN, puerto, número
2. Registrar el SBC en ACS
3. Configurar voice routes
4. Verificar estado "Online"

### Fase 3: Prueba de concepto

1. Llamada de prueba a un número interno del cliente
2. Verificar audio bidireccional
3. Verificar que OPTI responde correctamente

### Fase 4: Producción

1. Ajustes según resultados de prueba
2. Despliegue final
