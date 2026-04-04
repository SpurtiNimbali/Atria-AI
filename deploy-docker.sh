#!/usr/bin/env bash
# Atria AI — Elasticsearch + API + nginx UI in Docker (single host).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ ! -f ".env" ]; then
  echo "No .env — copying env.example (edit OPENAI_API_KEY, JINA_API_KEY, etc.)"
  cp env.example .env
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker is not running. Start Docker Desktop and retry."
  exit 1
fi

docker compose --profile fullstack up -d --build

echo ""
echo "Atria AI (Docker full stack)"
echo "  UI (nginx + API proxy):  http://localhost:8080"
echo "  API (direct):            http://127.0.0.1:8000"
echo "  Elasticsearch:           http://localhost:9200"
echo "  Kibana:                  http://localhost:5601"
echo ""
echo "Index demo patient (once ES is up):"
echo "  docker compose exec api sh -c 'cd agent && python ingest_synthetic.py synthetic_patient.json'"
echo ""
echo "Stop: docker compose --profile fullstack down"
