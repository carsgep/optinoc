#!/bin/bash
# ==============================================================================
# Detener servicios del PoC SBC Simulado
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=============================================="
echo "  Deteniendo PoC SBC Simulado"
echo "=============================================="

cd "$PROJECT_DIR"

# Detener contenedores
echo "Deteniendo contenedores..."
docker compose down

echo ""
echo "Contenedores detenidos."
echo ""
echo "Para eliminar volumenes (BORRA DATOS):"
echo "  docker compose down -v"
