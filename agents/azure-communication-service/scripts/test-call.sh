#!/bin/bash
# Test outbound call

set -e

SERVER_URL=${1:-http://localhost:8000}
TARGET_NUMBER=${2:-"+573001234567"}
TARGET_TYPE=${3:-"phone"}

echo "Testing outbound call..."
echo "Server: $SERVER_URL"
echo "Target: $TARGET_NUMBER"
echo "Type: $TARGET_TYPE"
echo ""

curl -X POST "$SERVER_URL/calls/outbound" \
  -H "Content-Type: application/json" \
  -d "{\"target_number\": \"$TARGET_NUMBER\", \"target_type\": \"$TARGET_TYPE\"}" \
  | jq .

echo ""
echo "Call initiated. Check server logs for details."
