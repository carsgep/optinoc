# Azure Communication Services - Precios y Costos

> Ultima actualizacion: Enero 2026

## Resumen Ejecutivo

**Azure Communication Services NO tiene costos fijos de infraestructura.** Es 100% pay-as-you-go (pagas solo por uso).

### Costos para este Proyecto

| Item | Costo |
|------|-------|
| Infraestructura base ACS | **$0** |
| Call Automation SDK | **$0** |
| Habilitar Teams Interoperability | **$0** |
| Llamada a usuario de Teams (bot participa) | **$0.004/min** |
| Llamada a usuario de Teams (usuario side) | **$0** (cubierto por M365) |

---

## 1. Infraestructura Base

### NO HAY COSTOS FIJOS

- ✅ **$0** renta mensual
- ✅ **$0** por crear el recurso ACS
- ✅ **$0** por tener el servicio activo
- ✅ **$0** por Call Automation SDK
- ✅ Solo pagas por uso real

**Modelo:** Pay-as-you-go puro

---

## 2. Costos por Uso

### Voice/Video Calling (VoIP)

| Servicio | Precio |
|----------|--------|
| Llamada VoIP grupal | $0.004 por participante/minuto |
| Screen sharing | $0.004 por participante/minuto |
| Audio streaming | Incluido |

**Nota importante:** El bot/aplicacion que usa Call Automation SDK **NO paga** por participar en la llamada.

### Ejemplo Real:

```
Llamada de 10 minutos: Bot → Usuario de Teams
- Usuario de Teams: 10 min × $0.004 = $0.04
- Bot (Call Automation): $0.00 (gratis)
- TOTAL: $0.04 USD
```

---

## 3. Teams Interoperability

### Costos de Habilitacion

**$0 - Completamente gratis habilitar la integracion**

No hay costo adicional por:
- ✅ Federacion entre ACS y Teams tenant
- ✅ Configuracion de Teams Interop
- ✅ Uso de APIs de interoperabilidad

### Costos de Uso con Teams

| Usuario Type | Via Teams Client | Via ACS SDK |
|--------------|------------------|-------------|
| **Teams User (con M365)** | $0 | $0.004/min |
| **External User** | $0 | $0.004/min |
| **Bot ACS (Call Automation)** | N/A | $0 |

### Escenario: Bot llama a usuario de Teams

```
Participante               Costo        Razon
--------------------------------------------------
Usuario Teams (Desktop)    $0           Cubierto por licencia M365
Bot ACS (tu aplicacion)    $0.004/min   Participacion en llamada VoIP
--------------------------------------------------
TOTAL POR MINUTO:          $0.004
```

### Mensajeria/Chat con Teams

| Accion | Teams User | External User via SDK |
|--------|------------|-----------------------|
| Enviar mensaje | $0 | $0.0008 |
| Recibir mensaje | $0 | $0 |

---

## 4. Llamadas PSTN (Telefonos Tradicionales)

**Para el escenario "fuera de horario"**

### Llamadas Salientes PSTN

| Concepto | Costo |
|----------|-------|
| Renta de numero telefonico | ~$1-2 USD/mes |
| Llamada saliente (varía por pais) | $0.012 - $0.10/min |
| Direct Routing (SIP) | $0.004/min |

### Llamadas Entrantes PSTN

| Tipo | Costo |
|------|-------|
| Inbound PSTN (toll-free) | $0.0220/min |
| Direct Routing inbound | $0.004/min |

**Nota:** Para tu proyecto, las llamadas PSTN son opcionales (solo fuera de horario).

---

## 5. Servicios Adicionales

### Grabacion de Llamadas

| Formato | Precio |
|---------|--------|
| Mixed audio | $0.002/min |
| Mixed audio/video | $0.01/min |
| Unmixed audio | $0.0012/participante/min |

### Otros Servicios

| Servicio | Precio |
|----------|--------|
| Closed Captions | Variable/min |
| SMS (USA) | $0.0075/mensaje |
| Chat messages | $0.0008/mensaje |
| Email | Variable |

---

## 6. Requisitos de Licenciamiento

### Para Teams Interoperability

**Requerido:**

1. **Teams Phone License** para usuarios que recibiran llamadas
   - Incluida en Microsoft 365 E5
   - O Teams Phone standalone license

2. **Enterprise Voice habilitado** (via PowerShell):
   ```powershell
   Set-CsPhoneNumberAssignment -Identity <user> -EnterpriseVoiceEnabled $true
   ```

3. **Permisos de Admin de Teams** para:
   - Habilitar federacion ACS-Teams tenant
   - Configurar `Set-CsTeamsAcsFederationConfiguration`

**NO requerido:**
- ❌ Licencia adicional por "Teams Interop"
- ❌ Costo extra por federacion
- ❌ Numeros telefonicos de Azure (para Teams-only)

---

## 7. Estimaciones de Presupuesto

### Escenario: Solo Llamadas a Teams (Horario Laboral)

| Volumen Mensual | Promedio/Llamada | Costo Mensual |
|-----------------|------------------|---------------|
| 100 llamadas | 5 minutos | **$2.00** |
| 500 llamadas | 5 minutos | **$10.00** |
| 1,000 llamadas | 5 minutos | **$20.00** |
| 5,000 llamadas | 5 minutos | **$100.00** |

**Calculo:** Llamadas × Minutos × $0.004

### Escenario: Mixto (Teams + PSTN)

Asumiendo:
- 70% llamadas Teams (horario laboral)
- 30% llamadas PSTN (fuera de horario)
- Promedio 5 min/llamada
- 1,000 llamadas/mes

```
Teams:  700 llamadas × 5 min × $0.004 = $14.00
PSTN:   300 llamadas × 5 min × $0.050 = $75.00 (estimado)
Renta numero:                           $2.00
--------------------------------------------------
TOTAL ESTIMADO:                         $91.00/mes
```

---

## 8. Facturacion y Precision

### Precision de Cobro

- ✅ **Facturacion al milisegundo**
- ✅ No hay redondeos a minuto completo
- ✅ Ejemplo: Llamada de 30 segundos = $0.002

### Data Egress

- ✅ **Azure Communication Services NO cobra** por transferencia de datos salientes
- ✅ El audio streaming esta incluido en el precio por minuto

---

## 9. Costos NO Incluidos

**Otros servicios Azure que podrias necesitar:**

| Servicio | Uso en Proyecto | Costo Estimado |
|----------|-----------------|----------------|
| Azure Blob Storage | Grabaciones | ~$0.02/GB/mes |
| OpenAI Realtime API | IA conversacional | Variable (ver OpenAI pricing) |
| Azure App Service | Hosting FastAPI | $0 - $50+/mes |
| Cognitive Services | TTS/STT (opcional) | Pay-as-you-go |
| ngrok (desarrollo) | Tunneling local | $0 - $8/mes |

---

## 10. Optimizacion de Costos

### Tips para Reducir Costos

1. **Usa Teams en horario laboral** ($0.004/min vs $0.05+/min PSTN)
2. **Monitorea duracion de llamadas** - cortarlas eficientemente
3. **Evita PSTN cuando sea posible** - 10x mas caro que Teams
4. **No grabes todo** - solo llamadas necesarias
5. **Usa VAD eficiente** - evita silencios largos facturados

### Alertas Recomendadas

Configura alertas de Azure cuando:
- Gasto mensual > $X USD
- Llamadas PSTN > X minutos
- Duracion promedio > X minutos

---

## 11. Referencias Oficiales

- [Azure Communication Services Pricing](https://azure.microsoft.com/en-us/pricing/details/communication-services/)
- [Pricing scenarios for Calling](https://learn.microsoft.com/en-us/azure/communication-services/concepts/pricing)
- [Teams Interoperability Pricing](https://learn.microsoft.com/en-us/azure/communication-services/concepts/pricing/teams-interop-pricing)
- [PSTN Pricing](https://learn.microsoft.com/en-us/azure/communication-services/concepts/pstn-pricing)
- [Azure Pricing Calculator](https://azure.microsoft.com/en-us/pricing/calculator/)

---

## 12. Resumen para Presupuesto Empresarial

### Costos Unicos
- **$0** - No hay setup fee

### Costos Fijos Mensuales
- **$0 - $2** - Solo si compras numero PSTN

### Costos Variables (Principales)
- **$0.004/min** por llamada a Teams (lado bot)
- **$0.02 - $0.10/min** por llamada PSTN (varía por país)

### Proyeccion Conservadora (1,000 llamadas/mes)
```
Mejor caso (100% Teams):     $20/mes
Caso mixto (70/30):          $91/mes
Peor caso (100% PSTN):       $250+/mes
```

**Recomendacion:** Comenzar con Teams-only para validar solucion con minimo costo.

---

## Notas Importantes

1. **Los precios son ilustrativos** - verificar precios actuales en portal Azure
2. **Pueden variar por region** - Colombia puede tener tarifas diferentes
3. **Precision al milisegundo** - no hay minimo de 1 minuto
4. **Sin compromisos** - puedes pausar/detener cuando quieras
5. **Teams Interop es gratuito** - solo pagas por participacion del bot

---

**Ultima revision:** Enero 6, 2026
**Fuente:** Microsoft Learn + Azure Pricing Portal
