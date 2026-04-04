# Get a working HTTPS link — handoff

I can’t log into your accounts or pay for hosting from here. Everything below is what’s **already in the repo** vs what **you** must click/type once.

## Already done in this repo

- **`docker-compose.deploy.yml`** — Elasticsearch + API + nginx (one machine = one URL on port **8080**).
- **API** can auto-ingest demo patient **`synthetic-001`** when `AUTO_INGEST_SYNTHETIC_DEMO=1` (set in that compose file).
- **Nginx** uses **`API_UPSTREAM`** (`api:8000` in Compose, or **`api.railway.internal:8000`** on Railway) so split cloud services work.
- **API container listens on port 8000** (fixed) so Railway private URLs stay predictable.

---

## Path A — Fastest “real” link: small VPS (~\$5–6/mo)

**You do:**

1. Create an Ubuntu VPS (DigitalOcean, Hetzner, Lightsail, etc.).
2. Install Docker: `curl -fsSL https://get.docker.com | sh`.
3. On the server:
   ```bash
   git clone https://github.com/YOUR_USER/YOUR_REPO.git && cd YOUR_REPO
   cp env.example .env
   nano .env   # set OPENAI_API_KEY and JINA_API_KEY
   docker compose -f docker-compose.deploy.yml up -d --build
   ```
4. Point a **domain** at the server’s IP (optional but recommended).
5. Install **Caddy**, copy **`Caddyfile.example`** → `/etc/caddy/Caddyfile`, uncomment **Option A**, set your domain to `reverse_proxy 127.0.0.1:8080`, reload Caddy.

**You share:** `https://your-domain` (or `http://SERVER_IP:8080` for a quick insecure test).

**Firewall:** open **80** and **443** (and **22** for SSH). Do **not** expose **9200**.

---

## Path B — Railway (no VPS; needs enough RAM)

Railway treats **each Compose service as its own service** (not one `docker compose up`). Create **three** services in **one project**, same environment.

**You do:**

### 0. Push this repo to GitHub and sign in to [railway.app](https://railway.app) with GitHub.

### 1. Service: `elasticsearch`

- **New** → **Docker Image** → `docker.elastic.co/elasticsearch/elasticsearch:8.11.0`
- **Name the service exactly:** `elasticsearch` (important for DNS).
- **Variables:**
  - `discovery.type` = `single-node`
  - `xpack.security.enabled` = `false`
  - `ES_JAVA_OPTS` = `-Xms256m -Xmx256m`
- **Volumes:** add volume, mount path **`/usr/share/elasticsearch/data`**
- **Networking:** do **not** generate a public domain (keep internal only).

### 2. Service: `api`

- **New** → **GitHub Repo** → this repo  
- **Root directory:** `backend`  
- **Variables** (minimum):
  - `ELASTIC_URL` = `http://elasticsearch.railway.internal:9200`
  - `OPENAI_API_KEY` = *(your key)*
  - `JINA_API_KEY` = *(your key)*
  - `AUTO_INGEST_SYNTHETIC_DEMO` = `1`
- Optional: `ELEVENLABS_API_KEY`, `ALLOWED_ORIGINS` (only if you split UI elsewhere).
- **Networking:** no public domain.
- In **Settings → Deploy**, ensure nothing overrides the listen port: the image listens on **8000**. If Railway sets `PORT` to something else, set **`PORT=8000`** in Variables.

### 3. Service: `web`

- **New** → **GitHub Repo** → same repo  
- **Root directory:** `web`  
- **Variables:**
  - `API_UPSTREAM` = `api.railway.internal:8000`
- **Networking → Generate domain** → this is the link you share (`https://….up.railway.app`).

### 4. Wait

First deploy can take **several minutes** (Elasticsearch yellow/green, then API ingest, then web). Check **Deploy logs** for each service.

**If things crash / OOM:** upgrade Railway resources or use **Path A**.

---

## Path C — Share your laptop (temporary)

**You do:** With Docker full stack running on **8080**, run `ngrok http 8080` and share the HTTPS URL. Your PC must stay on; keys are exposed to anyone with the link — demos only.

---

## What to send testers

- **URL:** your Railway domain or VPS HTTPS URL  
- **Patient ID:** `synthetic-001`  
- **Disclaimer:** Not medical advice — educational / planning support only.

---

## If you’re stuck

Paste **which path (A/B/C)** you’re on and the **last 30 lines of logs** from the failing service (API, web, or Elasticsearch).
