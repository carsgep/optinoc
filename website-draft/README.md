# Optimize IT Web completa de revisión

Borrador independiente del sitio corporativo, con HOME visual y nueve landings. Rama `feature/optimizeit-home-v2`. La web de optimizeit.co no se modifica.

Vista de revisión: https://optimizeit-home-borrador.optimize-it-0119.chatgpt.site/home-v2/

## Contenido y rutas

`/` y `/home-v2/` muestran el HOME. Las páginas bajo `/soluciones/` son: `protect-recover`, `cloud`, `infrastructure`, `managed-services`, `itsm`, `optinoc`, `optidesk`, `backup-as-a-service` y `cleanshield`.

El HOME conserva el carrusel visual de seis servicios, con rotación de 10 segundos y pausa al leer. El directorio, el menú y el footer dan acceso a las nueve páginas. Las landings incluyen portada con imagen, alcance, enfoque, tecnologías, preguntas frecuentes, servicios relacionados y formulario. OptiNOC también muestra una captura real del producto.

Los textos proceden del documento elaborado con Optimize IT en octubre de 2026. ITSM explica consultoría ITIL, análisis de brechas y Maximo IT o GLPI. Los servicios gestionados administran plataformas del cliente; Backup as a Service incluye la solución completa. OptiNOC y Optidesk son desarrollos propietarios de IA.

## Edición

- `content/landing-copy.json`: textos de las nueve páginas.
- `content/landings.ts`: categorías, imágenes, tecnologías y relaciones.
- `content/solutions.ts`: contenido y evidencias del recorrido del HOME; reutiliza textos de las landings.
- `content/visuals.ts`: imágenes y titulares del carrusel.
- `components/ServiceLanding.tsx`: composición de las páginas y casos anónimos.
- `components/ServiceCards.tsx`: directorio y servicios relacionados.
- `components/AdvisoryForm.tsx`: formulario de demostración.
- `components/SiteChrome.tsx`: navegación y footer.
- `app/landings.css`: estilos nuevos, que conservan los tokens navy, azul y verde del HOME.

## Imágenes

Los seis visuales originales y los tres nuevos se guardan en `public/media/solutions/<slug>/hero-v3.webp` y `hero-v3-mobile.webp`. Son escenas conceptuales generadas, no instalaciones reales ni interfaces del producto. Los prompts están en `content/image-prompts.json` y `content/landing-image-prompts.json`. La captura `public/media/solutions/optinoc/dashboard.webp` procede de la página pública del producto.

## Ejecución y comprobación

```sh
pnpm install --frozen-lockfile
pnpm dev
pnpm lint
pnpm build
node scripts/preview.cjs
# En otra terminal, con el servidor estático en el puerto 3001:
pnpm test
```

Next.js genera la exportación en `out/`. El test vigente es `scripts/qa-landings.cjs`, con Edge headless en Windows. Comprueba nueve rutas, contenido, imágenes, formulario, FAQ, navegación móvil, accesibilidad WCAG A/AA automática, ancho a 320 y 390 píxeles y carrusel de 10 segundos. Capturas e informe en `qa-artifacts/landings/` (no versionados). El script `qa.cjs` es una prueba histórica del diseño anterior, disponible como `test:legacy`; no describe esta versión.

## Estado de la entrega

Es una versión completa para revisar el diseño y el recorrido del sitio. El formulario valida campos y muestra una respuesta de demostración; no almacena ni transmite datos ni afirma haber enviado una solicitud. Antes de usarlo comercialmente se debe definir receptor o CRM, responsable de atención y política de datos.

`site.draft` mantiene noindex y nofollow. El enlace de revisión tiene acceso público; noindex no es un control de acceso. Casos, métricas, certificaciones, permisos de logos, cobertura y SLA deben concretarse antes del lanzamiento corporativo. Las cifras antiguas del HOME conservan su nota de contexto; no son garantías de servicio.

No copiar `out/` a la raíz del hosting corporativo sin revisar destino y rutas. Sites aloja una copia separada; no hay conexión a cPanel ni credenciales de la web actual en este frontend.
