# CareFork

Conversational caregiver copilot: discharge-style context in Elasticsearch, FastAPI WebSocket backend, and a Vite/React UI. **Not medical advice** — educational and planning support only.

## Layout

| Piece | Path |
|--------|------|
| Elasticsearch (Docker) | `docker-compose.yml` |
| Full stack in Docker (ES + API + UI) | `docker compose --profile fullstack` |
| **Vercel UI + Docker API** | `docker compose --profile backend` — see **Vercel + Docker** below |
| API + agents | `backend/` (`main.py`, agent code in `backend/agent/`) |
| Web UI (Vercel: set root to `web`) | `web/` |
| Older trees | `_legacy/` |

## Prerequisites

- Docker (for Elasticsearch)
- Python 3.10+
- Node 18+

## Setup

```bash
cp env.example .env
# Edit .env: OPENAI_API_KEY, JINA_API_KEY, ELASTIC_* if not local defaults
./setup.sh
```

Or start everything in one go (after `.env` exists):

```bash
chmod +x start_system.sh setup.sh
./start_system.sh
```

### Full stack in Docker (deployable single host)

Requires a repo-root `.env` (copy from `env.example` and set API keys). Builds `backend/Dockerfile` + `web/Dockerfile`; nginx on **8080** proxies `/ws`, `/patients`, `/tts`, and `/health` to the API so the browser uses one origin.

```bash
chmod +x deploy-docker.sh
./deploy-docker.sh
```

Or manually:

```bash
cp env.example .env   # if needed; then edit keys
docker compose --profile fullstack up -d --build
```

After containers are healthy, index the demo patient once:

```bash
docker compose exec api sh -c 'cd agent && python ingest_synthetic.py synthetic_patient.json'
```

- **UI:** `http://localhost:8080`
- **API (direct):** `http://127.0.0.1:8000`
- Stop: `docker compose --profile fullstack down`

`docker compose up -d` **without** the profile still starts only Elasticsearch + Kibana (for local dev with `./start_system.sh` or manual backend/Vite).

Manual run (no Docker for API/UI):

```bash
docker compose up -d
cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd agent && python ingest_synthetic.py synthetic_patient.json   # demo patient synthetic-001
cd .. && chmod +x run_dev.sh && ./run_dev.sh
# (loads repo-root `.env` automatically; binds 127.0.0.1:8000)
# other terminal:
cd web && cp .env.example .env.local   # set VITE_BACKEND_URL if needed
npm install && npm run dev
```

- API: `http://127.0.0.1:8000` (health: `/health`)
- UI: `http://localhost:5173` (default Vite)
- Demo patient ID: `synthetic-001`

## Environment

| Variable | Role |
|----------|------|
| `AGENT_BACKEND` | `conversational` (default) or `multi` (orchestrator) |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins (include your Vercel URL in prod) |
| `PORT` / `GATEWAY_PORT` | API port (default 8000) |
| `ELASTIC_URL` | Elasticsearch base URL |
| `OPENAI_API_KEY`, `JINA_API_KEY` | LLM + embeddings |

Frontend: `web/.env.example` → `VITE_BACKEND_URL` (e.g. `https://your-api.vercel.app` in production).

## Vercel + Docker (recommended split)

**Idea:** Vercel serves the static/React app from `web/`; a VPS or any Docker host runs Elasticsearch + the FastAPI API.

### 1. GitHub

Push this repo (never commit `.env`).

### 2. Docker host (API + Elasticsearch)

On the machine that will run the backend (e.g. a small VPS with Docker):

```bash
git clone <your-repo-url> && cd <repo>
cp env.example .env
# Edit .env: OPENAI_API_KEY, JINA_API_KEY, and:
#   ALLOWED_ORIGINS=https://<your-project>.vercel.app
chmod +x deploy-backend-docker.sh
./deploy-backend-docker.sh
```

Then index the demo patient once:

```bash
docker compose exec api sh -c 'cd agent && python ingest_synthetic.py synthetic_patient.json'
```

- API listens on **8000** by default. For production, put **HTTPS** in front (Caddy, nginx, Traefik, or your cloud load balancer) and point it at `http://127.0.0.1:8000`.
- **Do not** expose Elasticsearch **9200** or Kibana **5601** to the public internet; keep them on a private network or firewall them.

### 3. Vercel (frontend)

1. **New Project** → import the same GitHub repo.  
2. **Root Directory:** `web`  
3. Framework: **Vite** (build `npm run build`, output `dist`).  
4. **Environment variable:** `VITE_BACKEND_URL` = your **public HTTPS API origin** (e.g. `https://api.yourdomain.com`), no trailing slash.

Redeploy Vercel after changing `VITE_BACKEND_URL`.

### 4. CORS

The API must allow your Vercel origin. With `ALLOWED_ORIGINS` in the server `.env` (loaded by the `api` container), include exactly your preview/production URLs if they differ (comma-separated).

---

## Vercel only (UI)

- Root directory **`web`**, `VITE_BACKEND_URL` = your API’s public origin.  
- More hosting options for the API: `web/DEPLOYMENT.md`.

## Archived docs

Pitch decks, architecture write-ups, and older stack notes live under `_legacy/docs/`.
