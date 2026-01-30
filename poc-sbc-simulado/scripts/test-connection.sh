#!/bin/bash
# ==============================================================================
# Probar conexiones del PoC SBC
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"
source .env 2>/dev/null || true

echo "=============================================="
echo "  Pruebas de Conexion - PoC SBC"
echo "=============================================="

# Test 1: Docker containers
echo ""
echo "[1] Estado de contenedores Docker:"
echo "----------------------------------------------"
docker compose ps

# Test 2: Asterisk running
echo ""
echo "[2] Version de Asterisk:"
echo "----------------------------------------------"
docker compose exec -T freepbx asterisk -rx "core show version" 2>/dev/null || echo "ERROR: Asterisk no responde"

# Test 3: PJSIP Endpoints
echo ""
echo "[3] Endpoints PJSIP configurados:"
echo "----------------------------------------------"
docker compose exec -T freepbx asterisk -rx "pjsip show endpoints" 2>/dev/null || echo "ERROR: No se pueden listar endpoints"

# Test 4: PJSIP Registrations (Twilio)
echo ""
echo "[4] Registros SIP (Twilio):"
echo "----------------------------------------------"
docker compose exec -T freepbx asterisk -rx "pjsip show registrations" 2>/dev/null || echo "ERROR: No hay registros"

# Test 5: Transports
echo ""
echo "[5] Transportes SIP:"
echo "----------------------------------------------"
docker compose exec -T freepbx asterisk -rx "pjsip show transports" 2>/dev/null || echo "ERROR: No hay transportes"

# Test 6: DNS resolution to Microsoft
echo ""
echo "[6] Resolucion DNS a Microsoft PSTN Hub:"
echo "----------------------------------------------"
nslookup sip.pstnhub.microsoft.com 2>/dev/null || echo "ERROR: No se puede resolver DNS"

# Test 7: TLS connectivity to ACS (if configured)
echo ""
echo "[7] Conectividad TLS a Azure ACS:"
echo "----------------------------------------------"
if [ -n "$SBC_FQDN" ]; then
    echo "Probando conexion a sip.pstnhub.microsoft.com:5061..."
    timeout 5 openssl s_client -connect sip.pstnhub.microsoft.com:5061 </dev/null 2>/dev/null | head -5 || echo "WARN: No se pudo conectar (normal si no hay certificados)"
else
    echo "SKIP: SBC_FQDN no configurado"
fi

# Test 8: Ports listening
echo ""
echo "[8] Puertos escuchando:"
echo "----------------------------------------------"
docker compose exec -T freepbx netstat -tlnup 2>/dev/null | grep -E '5060|5061|10000' || echo "Verificando puertos..."

# Test 9: SIP OPTIONS to Twilio
echo ""
echo "[9] Test SIP OPTIONS a Twilio:"
echo "----------------------------------------------"
if [ -n "$TWILIO_SIP_DOMAIN" ]; then
    echo "Enviando SIP OPTIONS a $TWILIO_SIP_DOMAIN..."
    docker compose exec -T freepbx asterisk -rx "pjsip qualify twilio-trunk" 2>/dev/null || echo "WARN: Trunk twilio-trunk no existe aun"
else
    echo "SKIP: TWILIO_SIP_DOMAIN no configurado"
fi

echo ""
echo "=============================================="
echo "  Pruebas completadas"
echo "=============================================="
echo ""
echo "Si hay errores, verificar:"
echo "  1. .env tiene las credenciales correctas"
echo "  2. Trunks estan configurados en FreePBX web"
echo "  3. Firewall permite los puertos 5060, 5061, 10000-10100"
echo ""
