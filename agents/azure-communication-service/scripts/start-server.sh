#!/bin/bash
# Start FastAPI development server

set -e

cd "$(dirname "$0")/../../.."

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
fi

# Start server
echo "Starting FastAPI server on http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
