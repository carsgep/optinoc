# Puntos Previos - Configuracion del Sistema

Este documento contiene todos los pasos necesarios para configurar el sistema de llamadas con IA antes de ejecutar la aplicacion.

---

## Parte 1: Configuracion de Teams Interoperability

Esta configuracion se realiza **una sola vez** por tenant de Microsoft 365. Se ejecuta desde una maquina Windows con PowerShell (no desde la VM).

### 1.1 Instalar modulo de Microsoft Teams

```powershell
# Ejecutar PowerShell como Administrador
Install-Module -Name MicrosoftTeams -Force
```

### 1.2 Conectarse a Microsoft Teams

```powershell
Connect-MicrosoftTeams
```

Se abrira el navegador para autenticacion. Usar una cuenta con permisos de **Teams Administrator**.

### 1.3 Verificar configuracion actual

```powershell
Get-CsTeamsAcsFederationConfiguration
```

### 1.4 Habilitar usuarios de ACS en Teams

```powershell
Set-CsTeamsAcsFederationConfiguration -Identity Global -EnableAcsUsers $True
```

### 1.5 Agregar recurso ACS a la allowlist

```powershell
Set-CsTeamsAcsFederationConfiguration -Identity Global -AllowedAcsResources @('TU_ACS_RESOURCE_ID')
```

**IMPORTANTE:** Usar el **Immutable Resource ID (GUID)** del recurso ACS, no la ruta completa.

Para obtener el Resource ID:
1. Ir a Azure Portal
2. Navegar al recurso de Azure Communication Services
3. En Overview, copiar el **Immutable Resource ID**

### 1.6 Habilitar External Access Policy

```powershell
Set-CsExternalAccessPolicy -Identity Global -EnableAcsFederationAccess $true
```

### 1.7 Verificar que la configuracion quedo correcta

```powershell
Get-CsTeamsAcsFederationConfiguration
```

Resultado esperado:
```
Identity                       : Global
AllowedAcsResources            : {tu-resource-id-guid}
EnableAcsUsers                 : True
```

### 1.8 (Opcional) Habilitar Enterprise Voice para un usuario

Si se requiere que usuarios especificos puedan recibir llamadas de voz:

```powershell
Set-CsPhoneNumberAssignment -Identity "usuario@tudominio.com" -EnterpriseVoiceEnabled $true
```

**Nota:** Requiere licencia de Teams Phone.

---

## Parte 2: Obtener Object ID de usuarios de Teams

Para llamar a un usuario de Teams, necesitas su **Object ID** (GUID), no su email.

### Opcion A: Azure Portal

1. Ir a [portal.azure.com](https://portal.azure.com)
2. Navegar a **Microsoft Entra ID** (antes Azure AD)
3. Click en **Users**
4. Buscar el usuario por email
5. Copiar el **Object ID** del perfil

### Opcion B: Microsoft 365 Admin Center

1. Ir a [admin.microsoft.com](https://admin.microsoft.com)
2. **Users** → **Active users**
3. Click en el usuario
4. En la pestana "User", buscar el ID

### Opcion C: PowerShell

```powershell
# Conectarse a Azure AD
Connect-AzureAD

# Buscar usuario
Get-AzureADUser -SearchString "correo@empresa.com" | Select ObjectId, DisplayName, UserPrincipalName
```

### Opcion D: Microsoft Graph API

```bash
curl -X GET "https://graph.microsoft.com/v1.0/users/correo@empresa.com?$select=id,displayName" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN"
```

---

## Parte 3: Configuracion de Cloudflared en Ubuntu (VM)

Estos pasos se ejecutan en la maquina virtual Ubuntu donde correra la aplicacion.

### 3.1 Instalar cloudflared

```bash
# Descargar el paquete
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb

# Instalar
sudo dpkg -i cloudflared.deb

# Verificar instalacion
cloudflared --version

# Limpiar archivo descargado
rm cloudflared.deb
```

### 3.2 Autenticarse en Cloudflare

```bash
cloudflared tunnel login
```

Esto mostrara una URL como:
```
Please open the following URL and log in with your Cloudflare account:
https://dash.cloudflare.com/argotunnel?callback=...
```

**Pasos:**
1. Copiar la URL
2. Abrirla en el navegador de tu PC local (no en la VM)
3. Iniciar sesion en Cloudflare
4. Seleccionar el dominio que vas a usar
5. Click en "Authorize"

Veras en la terminal:
```
You have successfully logged in.
```

Esto crea el archivo `~/.cloudflared/cert.pem`

### 3.3 Crear el tunel

```bash
cloudflared tunnel create optinoc
```

**Guardar el Tunnel ID** que muestra. Ejemplo:
```
Created tunnel optinoc with id a1b2c3d4-e5f6-7890-abcd-1234567890ab
```

### 3.4 Crear carpeta de configuracion

```bash
mkdir -p ~/.cloudflared
```

### 3.5 Crear archivo de configuracion

```bash
nano ~/.cloudflared/config.yml
```

Contenido del archivo (reemplazar los valores):

```yaml
tunnel: TUNNEL_ID_AQUI
credentials-file: /home/TU_USUARIO/.cloudflared/TUNNEL_ID_AQUI.json

ingress:
  - hostname: optinoc.tudominio.com
    service: http://localhost:8000
  - service: http_status:404
```

**Valores a reemplazar:**
- `TUNNEL_ID_AQUI` → El UUID del paso 3.3
- `TU_USUARIO` → Tu usuario de Linux (ej: `adrian`, `ubuntu`, `azureuser`)
- `optinoc.tudominio.com` → Tu subdominio real

Guardar: `Ctrl+O`, `Enter`, `Ctrl+X`

### 3.6 Crear registro DNS en Cloudflare

```bash
cloudflared tunnel route dns optinoc optinoc.tudominio.com
```

Esto crea automaticamente un registro CNAME en tu dominio de Cloudflare.

### 3.7 Probar el tunel manualmente

```bash
cloudflared tunnel run optinoc
```

Resultado esperado:
```
INF Registered tunnel connection connIndex=0 ... location=xxx
```

Presionar `Ctrl+C` para detener.

---

## Parte 4: Configurar Cloudflared como Servicio del Sistema

Para que el tunel inicie automaticamente al reiniciar la VM.

### 4.1 Copiar configuracion al directorio del sistema

```bash
sudo mkdir -p /etc/cloudflared
sudo cp ~/.cloudflared/config.yml /etc/cloudflared/config.yml
sudo cp ~/.cloudflared/*.json /etc/cloudflared/
```

### 4.2 Actualizar rutas en config.yml del sistema

```bash
sudo nano /etc/cloudflared/config.yml
```

Cambiar la ruta del credentials-file:
```yaml
tunnel: TUNNEL_ID_AQUI
credentials-file: /etc/cloudflared/TUNNEL_ID_AQUI.json

ingress:
  - hostname: optinoc.tudominio.com
    service: http://localhost:8000
  - service: http_status:404
```

Guardar: `Ctrl+O`, `Enter`, `Ctrl+X`

### 4.3 Instalar el servicio

```bash
sudo cloudflared service install
```

### 4.4 Habilitar inicio automatico

```bash
sudo systemctl enable cloudflared
```

### 4.5 Iniciar el servicio

```bash
sudo systemctl start cloudflared
```

### 4.6 Verificar estado del servicio

```bash
sudo systemctl status cloudflared
```

Resultado esperado:
```
● cloudflared.service - cloudflared
     Loaded: loaded (/etc/systemd/system/cloudflared.service; enabled; ...)
     Active: active (running) since ...
```

### 4.7 Comandos utiles para el servicio

```bash
# Ver estado
sudo systemctl status cloudflared

# Reiniciar servicio
sudo systemctl restart cloudflared

# Detener servicio
sudo systemctl stop cloudflared

# Ver logs
sudo journalctl -u cloudflared -f
```

---

## Parte 5: Configuracion de la Aplicacion

### 5.1 Clonar el repositorio (si aplica)

```bash
git clone https://github.com/tu-repo/optinoc-bocc-realtime.git
cd optinoc-bocc-realtime
```

### 5.2 Crear entorno virtual de Python

```bash
python3 -m venv venv
source venv/bin/activate
```

### 5.3 Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5.4 Crear archivo .env

```bash
nano .env
```

Contenido:
```bash
# Azure Communication Services
ACS_CONNECTION_STRING=endpoint=https://tu-recurso.communication.azure.com/;accesskey=TU_ACCESS_KEY

# URL publica (tu dominio con cloudflared)
CALLBACK_URI=https://optinoc.tudominio.com

# Microsoft 365 Tenant ID
TENANT_ID=tu-tenant-id-guid

# OpenAI
OPENAI_API_KEY=sk-tu-api-key

# IBM DB2 (opcional)
DB2_USERNAME=usuario
DB2_PASSWORD=password
DB2_HOST_URL=ip-del-servidor
DB2_DATABASE=nombre_db
DB2_PORT=51000
```

Guardar: `Ctrl+O`, `Enter`, `Ctrl+X`

### 5.5 Ejecutar la aplicacion

```bash
python main.py
```

O con uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Parte 6: Verificacion Final

### 6.1 Verificar que el tunel esta activo

```bash
sudo systemctl status cloudflared
```

### 6.2 Verificar que la API responde

Desde tu PC local, abrir en navegador:
```
https://optinoc.tudominio.com/
```

Respuesta esperada:
```json
{"status":"VoiceBot API Running","acs_configured":true,"active_calls":0}
```

### 6.3 Probar una llamada a Teams

```bash
curl -X POST https://optinoc.tudominio.com/calls/outbound \
  -H "Content-Type: application/json" \
  -d '{
    "target_number": "OBJECT_ID_DEL_USUARIO",
    "target_type": "teams"
  }'
```

---

## Resumen de Archivos Importantes

| Archivo | Ubicacion | Descripcion |
|---------|-----------|-------------|
| `cert.pem` | `~/.cloudflared/` | Certificado de autenticacion de Cloudflare |
| `<tunnel-id>.json` | `~/.cloudflared/` o `/etc/cloudflared/` | Credenciales del tunel |
| `config.yml` | `~/.cloudflared/` o `/etc/cloudflared/` | Configuracion del tunel |
| `.env` | Raiz del proyecto | Variables de entorno de la aplicacion |

---

## Valores de Referencia (Configuracion Actual)

| Parametro | Valor |
|-----------|-------|
| Tenant ID | `27685d59-ac63-4a06-8bd6-3e743f5bd0a7` |
| ACS Resource ID | `cf65d038-b170-481e-a936-979aae677915` |
| ACS Endpoint | `https://acs-opti.unitedstates.communication.azure.com` |
| Dominio | `optimizeit.co` |

---

## Troubleshooting

### El tunel no conecta
```bash
# Ver logs del servicio
sudo journalctl -u cloudflared -f

# Verificar que el archivo de credenciales existe
ls -la /etc/cloudflared/
```

### La llamada falla inmediatamente
- Verificar que Teams Interoperability esta habilitado (Parte 1)
- Esperar 5-10 minutos despues de configurar (propagacion)
- Verificar que el Object ID del usuario es correcto

### Error 404 en la API
- Verificar que la aplicacion esta corriendo en puerto 8000
- Verificar que el tunel apunta a `http://localhost:8000`

### El usuario no recibe la llamada en Teams
- Verificar que el usuario tiene licencia de Teams
- Verificar que el Object ID es correcto (no el email)
- Verificar estado con `Get-CsTeamsAcsFederationConfiguration`

---

## Referencias

- [Azure Communication Services - Teams Interoperability](https://learn.microsoft.com/en-us/azure/communication-services/concepts/teams-interop)
- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)

---

*Documento creado: 2026-02-05*
*Ultima actualizacion: 2026-02-05*
