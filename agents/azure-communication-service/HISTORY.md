# Azure Communication Service - Historia del Proyecto

## Timeline

### Enero 2025

#### Semana 1-2: Setup Inicial
- Configuracion inicial del proyecto FastAPI
- Integracion basica con Azure Communication Services
- Primeras pruebas de llamadas salientes

#### Semana 3: Integracion OpenAI Realtime
- Implementacion de WebSocket bidireccional
- Conexion con OpenAI Realtime API
- Configuracion de VAD (Voice Activity Detection) server-side

#### Semana 4: Mejoras y Optimizaciones
- Cambio de modelo a `gpt-realtime-mini-2025-12-15` para optimizar costos
- Implementacion de control por voz con activacion "OPTI"
- Configuracion de Whisper para transcripcion

---

## Decisiones Tecnicas

### Modelo de IA
- **Decision:** Usar `gpt-realtime-mini-2025-12-15` en lugar de `gpt-4o-realtime`
- **Razon:** Reduccion significativa de costos manteniendo calidad aceptable
- **Fecha:** Enero 2025

### Tunnel de Desarrollo
- **Decision:** Usar cloudflared en lugar de ngrok
- **Razon:** Mejor integracion, sin limites de conexiones
- **Fecha:** Enero 2025

### Telefonia Fuera de Horario
- **Decision:** Usar Direct Routing de ACS con infraestructura Cisco del cliente
- **Razon:** Aprovechar infraestructura existente, mejor integracion empresarial
- **Alternativa descartada:** SIP trunking generico

### Nombre del Bot
- **Decision:** El asistente se llama "OPTI"
- **Razon:** Corto, facil de pronunciar, relacionado con Optimize IT
- **Comandos de voz:** "OPTI silencio", "OPTI habla"

---

## Problemas Resueltos

### Audio Bidireccional
- **Problema:** El audio no fluia correctamente en ambas direcciones
- **Solucion:** Habilitar `enable_bidirectional=True` en MediaStreamingOptions
- **Fecha:** Enero 2025

### Formato de Audio
- **Problema:** Incompatibilidad entre ACS (16kHz) y OpenAI (24kHz)
- **Solucion:** Implementar resampling de audio
- **Estado:** En progreso

---

## Cambios Importantes

| Fecha | Cambio | Commit |
|-------|--------|--------|
| 2025-01-14 | Cambio a modelo gpt-realtime-mini | 08ff56b |
| 2025-01-14 | Modelo mas economico | 3d696e7 |
| 2025-01-XX | Control por voz con OPTI | 46ef753 |
| 2025-01-XX | Cambio nombre bot en Teams | 0a38786 |
| 2025-01-XX | Comunicacion bidireccional funcionando | 9041f64 |

---

## Lecciones Aprendidas

1. **Media Streaming:** Siempre verificar que `enable_bidirectional=True` este configurado
2. **Callbacks:** El CALLBACK_URI debe ser accesible desde internet (usar cloudflared)
3. **Audio:** Considerar siempre la diferencia de sample rates entre servicios
4. **Costos:** Los modelos mini son suficientes para la mayoria de casos de uso
