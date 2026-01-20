#!/bin/bash
# List active calls

SERVER_URL=${1:-http://localhost:8000}

echo "Active calls on $SERVER_URL:"
echo ""

curl -s "$SERVER_URL/calls" | jq .
