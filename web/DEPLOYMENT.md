# Vercel Deployment Guide

## Frontend Deployment (Vercel)

### Prerequisites
1. Vercel account (sign up at https://vercel.com)
2. GitHub repository with your code

### Steps

1. **Install Vercel CLI** (optional, can also use web UI):
```bash
npm i -g vercel
```

2. **Set Environment Variables in Vercel Dashboard:**
   - Go to your project settings → Environment Variables
   - Add: `VITE_BACKEND_URL` = `https://your-backend-url.com`
   - For local dev, create `.env.local`:
     ```
     VITE_BACKEND_URL=http://localhost:8000
     ```

3. **Deploy via Vercel Dashboard:**
   - Go to https://vercel.com/new
   - Import your GitHub repository
   - Set **Root Directory** to: `web`
   - Framework Preset: **Vite**
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`
   - Click Deploy

4. **Or Deploy via CLI:**
```bash
cd web
vercel
```

## Backend Deployment

**⚠️ Important:** Vercel serverless functions don't support WebSockets well. Deploy your FastAPI backend separately:

### Recommended Options:

#### Option 1: Railway (Recommended for WebSockets)
1. Sign up at https://railway.app
2. Create new project → Deploy from GitHub
3. Select `backend` directory (or Dockerfile start `uvicorn main:app`)
4. Set environment variables:
   - `OPENAI_API_KEY`
   - `JINA_API_KEY`
   - `ELASTIC_URL`
   - `ELEVENLABS_API_KEY`
   - `ELEVENLABS_VOICE_ID`
   - `ELEVENLABS_MODEL_ID`
5. Railway will auto-detect Python and deploy
6. Update `VITE_BACKEND_URL` in Vercel with Railway URL

#### Option 2: Render
1. Sign up at https://render.com
2. Create new Web Service
3. Connect GitHub repo
4. Set root directory: `backend`
5. Build command: `pip install -r requirements.txt`
6. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
7. Add environment variables
8. Update `VITE_BACKEND_URL` in Vercel

#### Option 3: Fly.io
1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. In `gateway` directory: `fly launch`
3. Follow prompts
4. Add secrets: `fly secrets set OPENAI_API_KEY=...`
5. Update `VITE_BACKEND_URL` in Vercel

## Environment Variables

### Frontend (.env.local or Vercel):
```
VITE_BACKEND_URL=https://your-backend-url.com
```

### Backend (Railway/Render/Fly.io):
```
OPENAI_API_KEY=sk-...
JINA_API_KEY=jina_...
ELASTIC_URL=http://localhost:9200  # Or your Elasticsearch URL
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

## Post-Deployment

1. Update CORS in `backend/main.py` via env `ALLOWED_ORIGINS` (comma-separated), e.g. `https://your-app.vercel.app`
2. Test WebSocket connection
3. Test TTS endpoint
4. Verify all API calls work

## Troubleshooting

- **WebSocket not connecting**: Ensure backend supports WebSockets (Railway/Render/Fly.io)
- **CORS errors**: Set `ALLOWED_ORIGINS` in the API `.env` (see `backend/main.py`)
- **Environment variables not loading**: Ensure `VITE_` prefix for frontend vars
