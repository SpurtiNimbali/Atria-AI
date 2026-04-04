#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ ! -d venv ]; then
  python3 -m venv venv
fi
# shellcheck source=/dev/null
source venv/bin/activate
pip install -q -r requirements.txt
PORT="${PORT:-${GATEWAY_PORT:-8000}}"
exec uvicorn main:app --reload --host 127.0.0.1 --port "$PORT"
