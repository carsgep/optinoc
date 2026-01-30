#!/bin/bash
# ==============================================================================
# Setup inicial del PoC SBC Simulado
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=============================================="
echo "  PoC SBC Simulado - Setup Inicial"
echo "=============================================="

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker no esta instalado"
    echo "Instalar desde: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose no esta instalado"
    exit 1
fi

echo "[OK] Docker instalado"

# Verificar cloudflared (opcional)
if command -v cloudflared &> /dev/null; then
    echo "[OK] cloudflared instalado"
else
    echo "[WARN] cloudflared no instalado (opcional para tunnel)"
    echo "  Instalar: winget install --id Cloudflare.cloudflared"
fi

# Crear directorios necesarios
echo ""
echo "Creando directorios..."
mkdir -p "$PROJECT_DIR/certs"
mkdir -p "$PROJECT_DIR/config/custom"
mkdir -p "$PROJECT_DIR/logs"

# Verificar .env
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo ""
    echo "Copiando .env.example a .env..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "[IMPORTANTE] Editar .env con tus credenciales antes de continuar"
    echo "  - TWILIO_* : Credenciales de Twilio"
    echo "  - SBC_FQDN : Tu dominio para el SBC"
    echo "  - ACS_CONNECTION_STRING : Connection string de Azure ACS"
else
    echo "[OK] .env ya existe"
fi

# Crear archivo de configuracion custom de Asterisk
cat > "$PROJECT_DIR/config/custom/pjsip_custom.conf" << 'EOF'
; ==============================================================================
; Configuracion PJSIP Custom para PoC
; ==============================================================================
; Este archivo se carga despues de la configuracion de FreePBX
; Agregar aqui configuraciones adicionales si es necesario
; ==============================================================================

; Habilitar TLS para conexiones hacia ACS
[global]
type=global
; user_agent=Optinoc-SBC-PoC/1.0

; Transporte TLS para Azure ACS
[transport-tls]
type=transport
protocol=tls
bind=0.0.0.0:5061
; cert_file=/certs/fullchain.pem
; priv_key_file=/certs/privkey.pem
; ca_list_file=/certs/ca-bundle.crt
method=tlsv1_2
EOF

echo "[OK] Configuracion custom de Asterisk creada"

# Crear archivo .gitkeep para certs
touch "$PROJECT_DIR/certs/.gitkeep"

# Mensaje final
echo ""
echo "=============================================="
echo "  Setup completado!"
echo "=============================================="
echo ""
echo "Proximos pasos:"
echo ""
echo "1. Editar .env con tus credenciales"
echo "   nano $PROJECT_DIR/.env"
echo ""
echo "2. Obtener certificados SSL (una de estas opciones):"
echo "   a) Let's Encrypt:"
echo "      certbot certonly --standalone -d sbc-poc.tudominio.com"
echo "   b) Cloudflare Origin Certificate (si usas CF)"
echo ""
echo "3. Copiar certificados a ./certs/"
echo "   cp fullchain.pem $PROJECT_DIR/certs/"
echo "   cp privkey.pem $PROJECT_DIR/certs/"
echo ""
echo "4. Iniciar servicios:"
echo "   $SCRIPT_DIR/start.sh"
echo ""
echo "5. Acceder a FreePBX:"
echo "   http://localhost:8080"
echo ""
