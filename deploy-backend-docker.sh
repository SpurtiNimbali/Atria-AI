#!/usr/bin/env bash
# CareFork — Elasticsearch + API only (use with Vercel for the frontend).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ ! -f ".env" ]; then
  echo "No .env — copying env.example (edit OPENAI_API_KEY, JINA_API_KEY, ALLOWED_ORIGINS, etc.)"
  cp env.example .env
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker is not running. Start Docker Desktop and retry."
  exit 1
fi

docker compose --profile backend up -d --build

echo ""
echo "CareFork backend (Docker) — pair with Vercel (web/)"
echo "  API:              http://127.0.0.1:8000  (put HTTPS reverse proxy in front for production)"
echo "  Elasticsearch:  http://localhost:9200  (do not expose publicly; firewall this port)"
echo "  Kibana:           http://localhost:5601"
echo ""
echo "Set on the server .env:"
echo "  ALLOWED_ORIGINS=https://YOUR-APP.vercel.app"
echo ""
echo "Set in Vercel (web project):"
echo "  VITE_BACKEND_URL=https://YOUR-PUBLIC-API-ORIGIN   (no trailing slash)"
echo ""
echo "Index demo patient:"
echo "  docker compose exec api sh -c 'cd agent && python ingest_synthetic.py synthetic_patient.json'"
echo ""
echo "Stop everything from this compose file: docker compose down"
