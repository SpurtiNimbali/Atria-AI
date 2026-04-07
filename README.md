# Atria AI

Atria AI is a conversational caregiver copilot for post-discharge support. It combines:
- a Vite/React frontend
- a FastAPI WebSocket API
- Elasticsearch-backed patient context retrieval
- tool-augmented clinical reasoning workflows

All outputs are educational/planning support only. **Not medical advice.**

## Live demo

- Demo app: [https://atria-lp82jmdxg-spurtinimbalis-projects.vercel.app/](https://atria-lp82jmdxg-spurtinimbalis-projects.vercel.app/)
- Demo patient ID: `synthetic-001`

## Deployment guide

- Primary runbook: `DEPLOY_NOW.md`

## Architecture

### Runtime components

- `web/`: Vite + React UI
- `backend/main.py`: FastAPI app, `/health`, `/patients/*`, `/ws` endpoints
- `backend/agent/conversational_doctor.py`: core orchestration loop (tool-calling + streamed responses)
- `backend/agent/medical_tools.py`: deterministic medical tools (interactions, dosing, risk, KG, trials)
- `backend/agent/ehr_parser.py`: dashboard extraction from indexed EHR chunks
- `backend/agent/elastic_client.py`: ES connectivity layer

### Data plane

1. EHR FHIR bundle is normalized into chunks (`normalize.py`).
2. Chunks are embedded (Jina) and indexed to Elasticsearch (`ingest_synthetic.py` / `local_ingest.py`).
3. Query-time hybrid retrieval (BM25 + vector KNN) is executed (`search.py`).
4. Conversational agent synthesizes grounded answer with tool outputs and emits websocket events.
5. UI renders timeline, vitals, citations, and streamed assistant responses.

## API surface

- `GET /health` -> service health
- `GET /patients/{patient_id}/dashboard` -> structured dashboard payload from ES
- `POST /patients/{patient_id}/refresh` -> re-ingest patient data
- `POST /tts` -> ElevenLabs TTS passthrough
- `WS /ws` -> bidirectional query/response event stream

## Agent/tool capabilities (technical)

The live agent can call tools including:
- patient-document retrieval (`search_medical_literature`)
- drug interaction checks (`check_drug_interactions`)
- lab trend analysis + ML forecasting (`analyze_lab_trends`, `predict_lab_trend_ml`)
- treatment risk + dose calculations (`predict_treatment_risk`, `calculate_personalized_dose`)
- structured clinical knowledge queries (`query_knowledge_graph`)
- trial lookup (`search_clinical_trials`)
- pharmacogenomics checks (`check_genetic_compatibility`)
- scenario and progression simulation (`analyze_what_if_scenario`, `predict_disease_progression`)

## Repository layout

- `backend/` - API + agent runtime
- `web/` - frontend app
- `docker-compose.yml` - local/dev stack
- `docker-compose.deploy.yml` - deploy-oriented compose
- `railway-elasticsearch/` - Railway-specific ES wrapper image
- `_legacy/` - archived material

## Local development

### Option A: full stack in Docker

```bash
cp env.example .env
docker compose --profile fullstack up -d --build
docker compose exec api sh -c 'cd agent && python ingest_synthetic.py synthetic_patient.json'
```

Default URLs:
- UI: `http://localhost:8080`
- API: `http://127.0.0.1:8000`

### Option B: backend stack only (frontend on Vercel)

```bash
cp env.example .env
docker compose --profile backend up -d --build
docker compose exec api sh -c 'cd agent && python ingest_synthetic.py synthetic_patient.json'
```

## Configuration

### Backend env

- `OPENAI_API_KEY`
- `JINA_API_KEY`
- `ELASTIC_URL` (defaults vary by runtime)
- `ALLOWED_ORIGINS` (comma-separated CORS allowlist)
- `AUTO_INGEST_SYNTHETIC_DEMO` (`1` to auto-index demo bundle at startup)

Optional:
- `ELEVENLABS_API_KEY`
- `ELASTIC_API_KEY` / `ELASTIC_USER` / `ELASTIC_PASSWORD` (only when ES security is enabled)

### Frontend env

- `VITE_BACKEND_URL` must be the API origin only (no trailing slash)
  - Example: `https://api.example.com`

## Production notes

- For a stable split deployment, run API + ES on a VPS and serve UI on Vercel.
- Keep Elasticsearch non-public; do not expose `9200/9300/5601` on internet-facing firewall rules.
- On low-memory hosts (2GB), prefer running API + ES only; keep Kibana off unless needed.

## Safety

- No diagnosis/prescription guarantees.
- Cite source context when possible.
- Flag uncertainty or missing data explicitly.
- Always present outputs as educational planning support, not medical advice.
