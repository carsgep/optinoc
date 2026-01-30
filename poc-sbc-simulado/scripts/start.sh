#!/bin/bash
# ==============================================================================
# Iniciar servicios del PoC SBC Simulado
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=============================================="
echo "  Iniciando PoC SBC Simulado"
echo "=============================================="

cd "$PROJECT_DIR"

# Verificar .env
if [ ! -f ".env" ]; then
    echo "ERROR: .env no existe. Ejecutar setup.sh primero"
    exit 1
fi

# Cargar variables
source .env

# Iniciar contenedores
echo ""
echo "Iniciando contenedores Docker..."
docker compose up -d

# Esperar a que MariaDB este lista
echo ""
echo "Esperando a que la base de datos este lista..."
sleep 10

# Verificar estado
echo ""
echo "Estado de los contenedores:"
docker compose ps

# Mostrar logs iniciales
echo ""
echo "Logs de FreePBX (Ctrl+C para salir):"
echo "----------------------------------------------"
docker compose logs -f freepbx --tail=50 &
LOG_PID=$!

# Esperar un poco y luego detener logs
sleep 15
kill $LOG_PID 2>/dev/null || true

echo ""
echo "=============================================="
echo "  Servicios iniciados!"
echo "=============================================="
echo ""
echo "Accesos:"
echo "  - FreePBX Admin: http://localhost:8080"
echo "  - FreePBX HTTPS: https://localhost:8443"
echo ""
echo "Puertos expuestos:"
echo "  - SIP UDP: 5060 (para Twilio)"
echo "  - SIP TLS: 5061 (para Azure ACS)"
echo "  - RTP: 10000-10100 (audio)"
echo ""
echo "Comandos utiles:"
echo "  - Ver logs: docker compose logs -f freepbx"
echo "  - CLI Asterisk: docker compose exec freepbx asterisk -rvvv"
echo "  - Estado SIP: docker compose exec freepbx asterisk -rx 'pjsip show endpoints'"
echo ""
if [ -n "$CLOUDFLARE_TUNNEL_TOKEN" ]; then
    echo "Para iniciar Cloudflare Tunnel:"
    echo "  cloudflared tunnel run sbc-poc"
fi
