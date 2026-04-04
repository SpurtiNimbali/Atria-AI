# Get a working HTTPS link — handoff

I can’t log into your accounts or pay for hosting from here. Everything below is what’s **already in the repo** vs what **you** must click/type once.

## Already done in this repo

- **`docker-compose.deploy.yml`** — Elasticsearch + API + nginx (one machine = one URL on port **8080**).
- **API** can auto-ingest demo patient **`synthetic-001`** when `AUTO_INGEST_SYNTHETIC_DEMO=1` (set in that compose file).
- **Nginx** uses **`API_UPSTREAM`** (`api:8000` in Compose, or **`api.railway.internal:8000`** on Railway) so split cloud services work.
- **API container listens on port 8000** (fixed) so Railway private URLs stay predictable.

---

## “Free like Hugging Face?” — real talk

**Hugging Face Spaces (free)** is built for **one small app** (Gradio, one Docker image, tight RAM). This project is **Elasticsearch + FastAPI + nginx + WebSockets + a search index**. Putting **that exact stack** on a free Space either **won’t fit** (OOM / timeouts) or means **rebuilding** the product — which you don’t want.

**What can still be \$0:**

| Option | Cost | Catch |
|--------|------|--------|
| **Cloudflare Tunnel** or **ngrok** (free tier) | \$0 for the tunnel | You run Docker on **your** PC; link works **while the machine is on**; same app, no cuts. |
| **Oracle Cloud “Always Free”** ARM VM | \$0 for the VM (if approved) | Annoying signup; then it’s the same as Path A commands on **their** free server. |
| **OpenAI + Jina** | Not free | Usage is billed by those APIs — that’s separate from “hosting.” |

There is **no magic** that gives a **24/7 public link** for **this full stack** forever at **\$0** with **zero** tradeoff — something gives (your laptop, Oracle approval, or a few \$/mo VPS).

**Closest to “free + same app”:** **Path C** below with **Cloudflare Tunnel** (free, stable URLs possible with a free Cloudflare account) or **ngrok**.

---

## Path A — Recommended: small VPS + Docker + Caddy (~\$5–6/mo)

Use **Ubuntu 22.04/24.04** and **≥ 2 GB RAM** (Elasticsearch needs headroom). Providers: **Hetzner**, **DigitalOcean**, **Lightsail**, etc.

### 1. Create the VPS

Note the **public IP**. Allow **SSH (22)** in the provider firewall; you’ll open **80/443** on the machine with `ufw` after Caddy.

### 2. Install Docker

```bash
sudo apt update && sudo apt install -y ca-certificates curl
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Log out and SSH back in (or run `newgrp docker`) so `docker` works without `sudo`.

### 3. Clone repo + `.env`

```bash
git clone https://github.com/YOUR_USER/YOUR_REPO.git
cd YOUR_REPO
cp env.example .env
nano .env   # set OPENAI_API_KEY and JINA_API_KEY
```

### 4. Start the stack (app listens on **8080** on the server)

```bash
docker compose -f docker-compose.deploy.yml up -d --build
```

First boot: wait **2–5 minutes**. Then:

```bash
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/
curl -s http://127.0.0.1:8000/health
```

You should see **200** and `{"status":"healthy"}`.

### 5. DNS (recommended)

**A record:** `app.yourdomain.com` → **VPS IP** (names vary; use a subdomain you like).

### 6. Caddy (automatic HTTPS)

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy
```

`/etc/caddy/Caddyfile` — replace the domain:

```caddy
app.yourdomain.com {
    reverse_proxy 127.0.0.1:8080
}
```

```bash
sudo systemctl reload caddy
```

### 7. Firewall (`ufw`)

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

Never expose **9200** / **9300** / **5601** to the internet.

### 8. Share

**`https://app.yourdomain.com`** — full app, same behavior as local Docker.

**No domain yet:** `http://VPS_IP:8080` for a quick HTTP smoke test only.

---

## Path D — **Vercel (UI) + Railway (API + Elasticsearch)** ← you want this

**Two URLs:** `https://….vercel.app` (frontend) + `https://….up.railway.app` (API). The UI calls the API using `VITE_BACKEND_URL`. **No nginx** on Railway.

### 1. GitHub

Push this repo (no `.env` in git).

### 2. Railway — same project, **two** services

Sign in at [railway.app](https://railway.app) → **New project** → **Empty project**.

#### Service A: `elasticsearch`

- **+ New** → **GitHub Repo** → this repo → **Root directory:** **`railway-elasticsearch`** (small wrapper around **`elasticsearch:8.11.0`** that `chown`s the data dir then starts ES as user **`elasticsearch`**).  
  - **Do not** set **`RAILWAY_RUN_UID`** here: **`RAILWAY_RUN_UID=0`** fixes volume permissions but **Elasticsearch 8 refuses to run as root** (`can not run elasticsearch as root`).  
  - **Alternative (no volume, quick demo):** **Docker Image** → **`elasticsearch:8.11.0`** only — data is **lost** on redeploy; skip **`RAILWAY_RUN_UID`**.
- **Name:** `elasticsearch`
- **Variables:**
  - `discovery.type` = `single-node`
  - `xpack.security.enabled` = `false`
  - `ES_JAVA_OPTS` = `-Xms256m -Xmx256m`
- **Volume (not under Settings):** **⌘K** / canvas → attach a **volume** at **`/usr/share/elasticsearch/data`** if you want persistence ([Using volumes](https://docs.railway.com/volumes)). Use the **`railway-elasticsearch`** build when you use a volume.
- **Networking:** **elasticsearch** → **Settings** → **Networking** → **do not** click **Generate Domain** (keep ES private; API uses `elasticsearch.railway.internal`).

#### Service B: `api`

- **+ New** → **GitHub Repo** → this repo  
- **Root directory:** `backend`  
- **Variables:**
  - `ELASTIC_URL` = `http://elasticsearch.railway.internal:9200`
  - `OPENAI_API_KEY` = *(your key)*
  - `JINA_API_KEY` = *(your key)*
  - `AUTO_INGEST_SYNTHETIC_DEMO` = `1`
  - Optional: `ELEVENLABS_API_KEY`
- **Networking → Generate domain** → copy the **`https://……up.railway.app`** URL (no trailing slash). This is your **API base URL**.

Wait until **api** deploy logs show healthy / ingest finished (first time ~few minutes after ES is up).

**CORS:** The API allows **`https://*.vercel.app`** by default (`ALLOW_VERCEL_CORS_REGEX`, on unless set to `0`). You can still set **`ALLOWED_ORIGINS`** to your exact production URL if you want.

### 3. Vercel — frontend only

1. [vercel.com](https://vercel.com) → **Add New Project** → import the **same** GitHub repo.  
2. **Root Directory:** `web`  
3. Framework: **Vite** (build `npm run build`, output `dist`).  
4. **Environment variables:**
   - `VITE_BACKEND_URL` = **only** your Railway API origin, e.g. `https://your-api.up.railway.app` (**no** trailing slash, **not** your `*.vercel.app` URL — mixing them breaks REST + **WebSockets**).  
5. **Deploy**. Open the **`*.vercel.app`** link.

After you change Railway’s API URL or redeploy, **rebuild** Vercel if `VITE_BACKEND_URL` changes (it’s baked in at build time).

### 4. Share

- **App (what people click):** `https://your-app.vercel.app`  
- **Demo patient:** `synthetic-001`  
- **Not medical advice** (disclaimer)

---

## Path B — All on Railway (UI + API + ES via nginx)

Railway treats **each Compose service as its own service** (not one `docker compose up`). Create **three** services in **one project**, same environment.

**You do:**

### 0. Push this repo to GitHub and sign in to [railway.app](https://railway.app) with GitHub.

### 1. Service: `elasticsearch`

- **New** → **GitHub Repo** → this repo → **Root directory:** **`railway-elasticsearch`**. (Or **Docker Image** `elasticsearch:8.11.0` **without** a volume for a throwaway demo.)
- **Name the service exactly:** `elasticsearch` (important for DNS).
- **Variables:**
  - `discovery.type` = `single-node`
  - `xpack.security.enabled` = `false`
  - `ES_JAVA_OPTS` = `-Xms256m -Xmx256m`
- **Volume:** **⌘K** / canvas → mount **`/usr/share/elasticsearch/data`**. Use **`railway-elasticsearch`** when a volume is attached; **never** `RAILWAY_RUN_UID=0` with stock ES 8 (root is blocked). ([docs](https://docs.railway.com/volumes))
- **Networking:** **Settings** → **Networking** → **do not** generate a public domain (internal only).

### 2. Service: `api`

- **New** → **GitHub Repo** → this repo  
- **Root directory:** `backend`  
- **Variables** (minimum):
  - `ELASTIC_URL` = `http://elasticsearch.railway.internal:9200`
  - `OPENAI_API_KEY` = *(your key)*
  - `JINA_API_KEY` = *(your key)*
  - `AUTO_INGEST_SYNTHETIC_DEMO` = `1`
- Optional: `ELEVENLABS_API_KEY`, `ALLOWED_ORIGINS`.
- **Networking:** no public domain (Path B); use **Generate domain** only if this API is public (see **Path D**).
- The container listens on Railway’s **`PORT`** (defaults to **8000** in Docker if unset).

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

## Path C — Share your laptop (temporary, **\$0** hosting)

Same Docker app as always — **no functionality change**. Only “hosting” is your machine + a tunnel.

### Option C1 — ngrok (quickest)

1. Run the stack: `docker compose -f docker-compose.deploy.yml up -d --build` (or `./deploy-docker.sh` if you use the profiled compose).
2. Install [ngrok](https://ngrok.com), then: `ngrok http 8080`
3. Share the **https://**.ngrok-free.app** link.

### Option C2 — Cloudflare Tunnel (free, nicer URLs with a domain)

1. Same as above: app on **localhost:8080**.
2. Install `cloudflared`, log in to Cloudflare, create a tunnel pointing to `http://localhost:8080`.
3. You can attach a **free** `*.trycloudflare.com` quick tunnel or your own domain.

**Tradeoffs:** PC must stay awake; anyone with the link hits **your** API keys usage; fine for demos / classmates, not production.

---

## What to send testers

- **URL:** your Railway domain or VPS HTTPS URL  
- **Patient ID:** `synthetic-001` (demo patient **Sophia Grace Doe** — data comes from **Elasticsearch** after ingest)  
- **Disclaimer:** Not medical advice — educational / planning support only.

**UI shows generic vitals / timeline but not Sophia’s EHR:** WebSockets can work while the **dashboard** (`GET /patients/synthetic-001/dashboard`) still has nothing to read. On Railway: ensure **`elasticsearch`** is **up** before **`api`** finishes booting, **`ELASTIC_URL`** is `http://elasticsearch.railway.internal:9200`, and **`AUTO_INGEST_SYNTHETIC_DEMO=1`**. Check **api** deploy logs for `AUTO_INGEST_SYNTHETIC_DEMO finished`. If ingest ran before ES was ready, **redeploy api** or call **`POST https://<your-api>/patients/synthetic-001/refresh`** once, then reload the Vercel app.

---

