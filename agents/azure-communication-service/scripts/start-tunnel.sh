#!/bin/bash
# Start cloudflared tunnel for development

set -e

PORT=${1:-8000}

echo "Starting cloudflared tunnel for http://localhost:$PORT"
echo "Copy the generated URL to CALLBACK_URI in .env"
echo ""

cloudflared tunnel --url http://localhost:$PORT
