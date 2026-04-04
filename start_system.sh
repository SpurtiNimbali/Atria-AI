#!/bin/bash
# CareFork — start Elasticsearch (Docker), ingest demo patient if needed, backend API, web UI

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "CareFork — local stack"
echo "========================================"
echo ""

if [ ! -f ".env" ]; then
    echo "No .env — copying env.example"
    cp env.example .env
    echo "${YELLOW}Edit .env and set OPENAI_API_KEY, JINA_API_KEY, etc.${NC}"
fi

if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Start Docker Desktop and retry."
    exit 1
fi

echo "Starting Elasticsearch..."
if docker compose version > /dev/null 2>&1; then
    docker compose up -d
else
    docker-compose up -d
fi

echo "Waiting for Elasticsearch..."
until curl -sf http://localhost:9200/_cluster/health > /dev/null 2>&1; do
    sleep 2
done
echo "${GREEN}Elasticsearch ready${NC}"

echo ""
echo "Python backend (venv in backend/)..."
cd "$ROOT/backend"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
if [ ! -f "venv/.packages_installed" ]; then
    pip install -q -r requirements.txt
    touch venv/.packages_installed
fi

PATIENT_EXISTS=$(curl -s "http://localhost:9200/ehr_chunks/_count?q=patient_id:synthetic-001" 2>/dev/null | grep -o '"count":[0-9]*' | head -1 | cut -d: -f2 || true)
PATIENT_EXISTS=${PATIENT_EXISTS:-0}
if [ "$PATIENT_EXISTS" = "0" ]; then
    echo "Ingesting synthetic patient (synthetic-001)..."
    cd "$ROOT/backend/agent"
    python3 ingest_synthetic.py synthetic_patient.json
    cd "$ROOT/backend"
else
    echo "${GREEN}Patient synthetic-001 already indexed ($PATIENT_EXISTS chunks)${NC}"
fi

echo ""
echo "Starting API on :8000..."
nohup uvicorn main:app --reload --host 127.0.0.1 --port 8000 > "$ROOT/backend.log" 2>&1 &
API_PID=$!
echo "${GREEN}API PID $API_PID (logs: tail -f backend.log)${NC}"

until curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; do sleep 1; done
echo "${GREEN}API healthy${NC}"

echo ""
echo "Starting web (Vite) on :5173..."
cd "$ROOT/web"
if [ ! -d "node_modules" ]; then
    npm install
fi
nohup npm run dev > "$ROOT/web.log" 2>&1 &
WEB_PID=$!
echo "${GREEN}Web PID $WEB_PID (logs: tail -f web.log)${NC}"

cd "$ROOT"
echo ""
echo "========================================"
echo "${GREEN}Ready${NC}"
echo "========================================"
echo "  Elasticsearch: http://localhost:9200"
echo "  API:            http://127.0.0.1:8000"
echo "  Web UI:         http://localhost:5173"
echo "  Patient ID:     synthetic-001 (Sophia Grace Doe)"
echo ""
echo "  AGENT_BACKEND=conversational (default) or multi — set in .env before starting API"
echo ""
echo "Stop: kill $API_PID $WEB_PID && docker compose down"
echo ""
