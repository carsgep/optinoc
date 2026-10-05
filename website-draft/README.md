# Optimize IT — HOME v2 (borrador)

Propuesta independiente en la rama **feature/optimizeit-home-v2** del repositorio `carsgep/optinoc`. La copia de revisión está alojada en https://optimizeit-home-borrador.optimize-it-0119.chatgpt.site/home-v2/. No se ha modificado el home existente de optimizeit.co. No hay formularios conectados, analítica externa ni credenciales de hosting.

## Inspección y decisiones técnicas

- El repositorio contiene Python/FastAPI, ACS, DB2 e infraestructura, pero no el frontend corporativo. Se conserva íntegro; todos los archivos nuevos están bajo `website-draft/`.
- La referencia pública `/optinoc2/` es HTML/CSS/JavaScript. Se reutilizaron colores, tipografías, contenido funcional, logo y captura del producto. No se copiaron el formulario PHP ni los scripts de seguimiento.
- Next.js 16.3.8, React y TypeScript, con exportación estática. El resultado podría servirse en cPanel sin servidor Node, tras revisar un destino separado y autorizar su publicación.
- CSS con tokens y componentes reutilizables en lugar de Tailwind, evitando una capa adicional para este sistema visual.
- No hay `app/page.tsx`: el borrador no reemplaza `/`. La rama se comparte en GitHub y una copia estática se aloja de forma independiente en Sites. No se hizo merge ni conexión a cPanel.

## Ejecución local

Node.js 20.9+ y pnpm. Validado con pnpm 11.19.

```sh
cd website-draft
pnpm install --frozen-lockfile
pnpm dev
```

Abrir `http://127.0.0.1:3000/home-v2/`. El servidor escucha únicamente en loopback. Ctrl+C lo detiene.

```sh
pnpm lint
pnpm typecheck
pnpm build
# Con el servidor local activo, en otra terminal:
pnpm test
```

Las pruebas utilizan un perfil temporal de Edge headless en Windows. En Linux, instalar Chromium mediante `pnpm exec playwright install chromium`. `QA_URL` permite apuntar a una copia local de la exportación estática. Informes y capturas: `qa-artifacts/` (no versionados).

El build genera `out/`. **No subir esta carpeta a la raíz de la web actual**: incluye recursos y robots de un sitio independiente. Un despliegue futuro exige revisar rutas y aislamiento del destino y contar con autorización del usuario.

Para revisar la exportación sin el servidor de desarrollo, ejecutar `node scripts/preview.cjs` y abrir `http://127.0.0.1:3001/home-v2/`. Esta vista también escucha solo en loopback.

## Rutas

- `/home-v2/`
- `/soluciones/protect-recover/`
- `/soluciones/cloud/`
- `/soluciones/optinoc/`
- `/soluciones/infrastructure/`
- `/soluciones/itsm/`
- `/soluciones/managed-services/`

Las páginas se generan con los mismos datos y componentes del carrusel. Las cuatro etapas están en su HTML estático. Cada solución tiene title, descripción, canonical, OpenGraph y Service JSON-LD.

Mientras `site.draft` sea `true`, las páginas llevan **noindex, nofollow** y robots bloquea la indexación. Esto no es un control de acceso: la copia alojada actualmente permite acceso público mediante su enlace. Cambiar esta bandera no publica ni activa formularios.

## Archivos creados y arquitectura

| Archivo                                                 | Responsabilidad                                                                    |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `content/site.ts`                                       | Copy global, navegación, hero, CTA, logo, redes y estado de borrador               |
| `content/solutions.ts`                                  | Modelo tipado, seis soluciones, evidencias, fuentes, métricas, casos y tecnologías |
| `components/Hero.tsx`                                   | Componente de la versión anterior; ya no se renderiza en HOME             |
| `components/SolutionsExperience.tsx`                    | Selector, timer, autoplay, swipe y teclado                                         |
| `components/Story.tsx`                                  | Historias, MarketEvidence, Capability cards, ExperienceMetrics y SuccessCaseCard   |
| `components/MediaBlock.tsx`                             | MediaBlock, ResponsiveImage y ResponsiveVideo                                      |
| `components/SiteChrome.tsx`                             | Navigation, CTA, diálogo local y Footer                                            |
| `components/Tracking.tsx`                               | Seguimiento local de visualización de casos                                        |
| `lib/analytics.ts`                                      | Adaptador para analítica futura                                                    |
| `app/home-v2/page.tsx`                                  | HOME alternativa                                                                   |
| `app/soluciones/[slug]/page.tsx`                        | Rutas individuales generadas desde contenido                                       |
| `app/globals.css`                                       | Tokens, responsive, layout y animaciones                                           |
| `app/layout.tsx`, `app/robots.ts`                       | Layout, metadata y estado de indexación                                            |
| `public/media/`                                         | Logo, dashboard optimizado y carpetas de las seis soluciones                       |
| `scripts/qa.cjs`                                        | Pruebas de comportamiento, responsive, rutas, SEO y accesibilidad                  |
| `scripts/optimize-assets.cjs`                           | Optimización del dashboard a WebP                                                  |
| `next.config.ts`, `tsconfig.json`, `eslint.config.mjs`  | Configuración técnica                                                              |
| `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml` | Dependencias reproducibles                                                         |

No se modifica ningún archivo preexistente del backend. Las carpetas `node_modules`, `.next`, `out` y `qa-artifacts` están ignoradas por Git.

## Decisiones de interacción

- Las seis soluciones se ven en escritorio; en móvil se muestran en una rejilla 3×2.
- Protect & Recover es la primera solución. El recorrido avanza cada 10 segundos de reproducción activa y vuelve a la primera al finalizar.
- Clic, controles anterior/siguiente, teclado o swipe entran en modo manual y cancelan el contador. Cambiar de etapa también detiene el recorrido.
- El ratón o foco dentro de la historia, y la pestaña oculta, pausan temporalmente el contador. Al salir se conserva el tiempo restante.
- El foco en el selector de soluciones también pausa el avance temporalmente, para que la selección no cambie mientras se navega con teclado.
- Reanudar inicia un intervalo nuevo. `prefers-reduced-motion` desactiva autoplay y animaciones.
- Flechas, Home y End funcionan en los selectores; el autoplay no mueve el foco. No hay encierro de foco en el carrusel.
- Las páginas individuales muestran las cuatro etapas seguidas para lectura, SEO y enlaces de campañas.
- Los CTA abren un diálogo de demostración local: no capturan ni envían datos.
- No se inventan casos de Cloud, ITSM u OptiNOC: su etapa de casos invita a definir un proyecto sin presentar resultados inexistentes.

## Cambiar textos, imágenes y videos

**Textos:** `content/site.ts` para copy general y `content/solutions.ts` para cada solución. Mantener el contenido en esos objetos, sin duplicarlo entre rutas.

**Carrusel inicial:** `content/visuals.ts` configura los titulares, imágenes y el intervalo de 10 segundos. Las seis imágenes están en `public/media/solutions/<slug>/hero-v3.webp` y `hero-v3-mobile.webp`. `content/image-prompts.json` conserva los prompts originales. Las imágenes son ilustraciones conceptuales generadas. Hacer clic para leer detiene el avance.

**Imágenes de las historias:** guardar WebP/AVIF en `public/media/solutions/<slug>/` y configurar `media`:

```ts
media: {
  type: 'image',
  src: '/media/solutions/cloud/arquitectura.webp',
  alt: 'Descripción precisa de la imagen',
  caption: 'Pie opcional',
}
```

**Videos:** mismo objeto con `type: 'video'`, `src` y `poster`. El componente incluye controles, `playsInline` y `preload="none"`, sin autoplay con sonido. Los videos con voz deberán incorporar subtítulos antes de publicación. El carrusel inicial utiliza las imágenes configuradas en `content/visuals.ts`.

**Logos:** `site.logo` para Optimize IT; los elementos de `technologies` admiten `logo: Media`. Actualmente los fabricantes se presentan por su nombre, sin recrear logos ni afirmar niveles de alianza.

**Añadir una solución:** agregar un objeto completo al array `solutions` con slug único; se generan la ruta y los enlaces del footer. Ajustar la rejilla del selector si el portafolio supera seis elementos.

**Estadísticas:** editar `evidence` con valor, etiqueta, contexto, fuente, URL y año. Identificar población y significado del dato. Máximo cuatro por solución. Los estudios de mercado no son resultados ni promesas de Optimize IT.

**Casos:** editar `cases` y sus referencias dentro de las soluciones. El modelo admite nombre y logo de cliente para una integración futura autorizada. No adjudicar tecnologías, sectores ni resultados adicionales sin evidencia. El caso de ransomware agrupa las dos recuperaciones informadas, sin inventar tiempos o porcentajes.

**CMS:** reemplazar los objetos locales por un adaptador validado que entregue el mismo modelo `Solution[]`; las páginas y componentes comparten ese contrato.

**Analítica:** `track()` emite `optimizeit:analytics` en el navegador. `setAnalyticsAdapter()` permite conectar un proveedor posteriormente. No transmite datos por sí solo. Eventos preparados: `solution_view`, `solution_select`, `solution_section_view`, `carousel_pause`, `carousel_resume`, `cta_click`, `success_case_view`.

## Validaciones pendientes antes del lanzamiento

- Primera implementación de IBM Storage Defender en Colombia: conservada con `requiresValidation: true`, sin mostrarla como hecho comercial.
- Implementación pionera de Predatar: mismo tratamiento.
- Nivel IBM Partner Plus Gold de Optimize IT: confirmar vigencia y permiso para usar el distintivo. Marcado para validación y no mostrado.
- Precisar período y alcance de las métricas corporativas y disponibilidad cloud. En el borrador se identifican como datos suministrados por Optimize IT, no como SLA contractuales.
- Autorizar publicación y documentar resultados de los casos. No aparecen nombres de bancos.
- Definir el canal comercial general y conectar los CTA. No se reutiliza el formulario de demos de OptiNOC para otras soluciones.

## Fuentes utilizadas

Contenido público consultado el 3 de octubre de 2026; revisión final iniciada el 4 de octubre. Los informes mantienen explícitamente su año 2025.

- [OptiNOC, contenido funcional y activos originales](https://www.optimizeit.co/optinoc2/).
- [Uptime Institute — Facility Outages and AI Integration 2025](https://datacenter.uptimeinstitute.com/rs/711-RIA-145/images/2025.AnnualSurvey.OutagesAI.3Pager.pdf?version=0): costos de interrupción (n=94) y prevención percibida mediante procesos/gestión (n=98). Es una encuesta de centros de datos, no exclusiva de ITSM.
- [IBM — Cost of a Data Breach 2025](https://newsroom.ibm.com/2025-07-30-ibm-report-13-of-organizations-reported-breaches-of-ai-models-or-applications%2C-97-of-which-reported-lacking-proper-ai-access-controls): US$4,44 millones, costo promedio global de una brecha, no de todo incidente.
- [CISA — StopRansomware Guide](https://www.cisa.gov/stopransomware/ransomware-guide): protección offline y pruebas de recuperación; referencia cualitativa.
- [Flexera — State of the Cloud 2025](https://info.flexera.com/CM-REPORT-State-of-the-Cloud-AWS): 759 encuestados; gasto, desperdicio estimado y MSP.
- [New Relic / ETR — Observability Forecast 2025](https://newrelic.com/press-release/20250917): 1.700 participantes, 23 países; tiempo de ingeniería dedicado a interrupciones.
- [IBM — Maximo IT 9.2](https://www.ibm.com/docs/en/max-it/cd.0.0_cd?topic=it-whats-new-in-maximo-v92): referencia cualitativa de servicios y activos, sin atribuir capacidades nuevas a instalaciones de clientes.
- [IBM Partner Plus](https://www.ibm.com/partnerplus/): nombre del programa; no acredita el nivel de Optimize IT.
- Experiencia, métricas corporativas y hechos de casos: documento suministrado por el usuario.

## Límites de las pruebas

Las comprobaciones automatizadas no sustituyen una revisión con lectores de pantalla ni métricas de campo de Core Web Vitals. La salida es estática, imágenes diferidas salvo el logo y videos sin descarga automática. No se ejecuta `test.py` del backend: corresponde a integraciones operativas ajenas al frontend aislado.

## Resultado de verificación de la versión anterior — 4 de octubre de 2026

Estos resultados preceden al nuevo carrusel visual. La revisión móvil y la suite funcional deben actualizarse y repetirse para esta versión; `scripts/qa.cjs` aún contiene expectativas del carrusel anterior de 15 segundos.

- Build estático, lint y TypeScript: correctos.
- 16 comprobaciones funcionales completadas sobre `out/`, incluyendo temporizador, pausa manual, reanudación, pausa por hover, retorno circular, teclado, swipe, menú móvil y reduced motion.
- Seis rutas con cuatro etapas, canonical, OpenGraph y JSON-LD comprobadas.
- Sin desbordamiento horizontal a 768, 390 y 320 px.
- Auditoría automática WCAG A/AA sin infracciones en la HOME, Protect & Recover y OptiNOC. No equivale a una certificación de accesibilidad.
- Sin errores de ejecución ni solicitudes fallidas en esa prueba.
- Laboratorio local, viewport móvil sin throttling: LCP inicial 320 ms y CLS 0,0096. No mide INP de campo ni garantiza esos tiempos en internet.
- Ningún archivo preexistente del repositorio fue modificado; toda la propuesta permanece en `website-draft/`.

Next.js genera además `AGENTS.md` y `CLAUDE.md` dentro del nuevo proyecto con instrucciones para futuras ediciones.

## Entrega a otro desarrollador

El frontend está íntegramente en `website-draft/`, en la rama `feature/optimizeit-home-v2`. Para entregar solo el frontend, exportar esta carpeta como ZIP; no necesita los archivos Python ni la configuración del backend. Para colaborar mediante GitHub, dar acceso al repositorio completo o utilizar un repositorio independiente para esta carpeta.
