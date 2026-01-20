#!/bin/bash
# Check server status and business hours

SERVER_URL=${1:-http://localhost:8000}

echo "=== Server Status ==="
curl -s "$SERVER_URL/" | jq .

echo ""
echo "=== Health Check ==="
curl -s "$SERVER_URL/health" | jq .

echo ""
echo "=== Business Hours ==="
curl -s "$SERVER_URL/utils/business-hours" | jq .
