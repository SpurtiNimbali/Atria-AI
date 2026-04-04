#!/bin/bash
# CareFork — minimal local setup (no Modal): Docker ES + Python venv + web deps

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "CareFork setup"
echo "=============="

for cmd in python3 node docker; do
    command -v "$cmd" >/dev/null || { echo "Missing: $cmd"; exit 1; }
done

[ -f .env ] || cp env.example .env

if docker compose version >/dev/null 2>&1; then
    docker compose up -d
else
    docker-compose up -d
fi

echo "Waiting for Elasticsearch..."
until curl -sf http://localhost:9200/_cluster/health >/dev/null 2>&1; do sleep 2; done

cd "$ROOT/backend"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd "$ROOT/web"
npm install

echo ""
echo "Done. Next:"
echo "  1. Edit .env at repo root (OPENAI_API_KEY, JINA_API_KEY, …)"
echo "  2. ./start_system.sh   OR manually:"
echo "     cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000"
echo "     cd web && npm run dev"
echo ""
