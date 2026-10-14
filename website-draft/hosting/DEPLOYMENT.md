# Publicación corporativa en cPanel

Requiere PHP 8.1 o superior con PDO MySQL, HTTPS, una base de datos y usuario dedicado. No utiliza Node.js en el servidor.

1. Confirmar el document root real de optimizeit.co, la versión de PHP y los nombres completos de la base y usuario asignados por cPanel.
2. Descargar una copia completa de los archivos actuales y guardar la configuración de Apache y los índices actuales antes de modificar el sitio. No borrar servicios ni aplicaciones existentes.
3. Importar `schema.sql` en la base de contactos. Crea dos tablas con prefijo `optimizeit_`; no altera tablas existentes.
4. Instalar `contact-config.php`, basado en el ejemplo, fuera del directorio público: `<padre del document root>/optimizeit-private/contact-config.php`. Completar credenciales y secreto aleatorio en el servidor. No subir el ejemplo ni el SQL al directorio público. Si el hosting usa un addon domain con raíz anidada, revisar y ajustar la ubicación privada antes de publicar.
5. Generar la exportación con `NEXT_PUBLIC_PRODUCTION_SITE=true`, `NEXT_PUBLIC_SITE_ORIGIN=https://optimizeit.co` y `NEXT_PUBLIC_CONTACT_ENDPOINT=/api/contact.php`.
6. Copiar `out/` al document root, incluyendo `api/contact.php`. Preservar el índice anterior hasta verificar `/home-v2/` y las nueve rutas. Revisar cualquier `.htaccess` existente sin reemplazarlo automáticamente.
7. Probar el formulario con datos de prueba, verificar la inserción real en MySQL, los errores de validación y los reintentos sin duplicados. El éxito solo se muestra después de confirmar el registro.
8. Activar `index.html` como página principal y confirmar qué índice tiene prioridad en Apache. Mantener la copia del índice anterior para volver atrás. Verificar HTTPS, canonical, robots, navegación y registro de contactos después de activar.

Los contactos quedan en `optimizeit_contacts`. No hay endpoint público para consultarlos. Se consultan mediante acceso autenticado a la base. La recepción por email o integración con CRM no forma parte del almacenamiento actual. Las credenciales del hosting y de MySQL nunca se incluyen en las fuentes ni en el navegador.
