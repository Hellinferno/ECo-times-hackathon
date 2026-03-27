# 11 - Environment & DevOps

## AlphaHunter AI - Current Deployment Guide

## 1. Overview

AlphaHunter now targets a split deployment:

- Frontend: Vercel
- Backend: Railway
- Database: PostgreSQL
- Cache: Redis
- LLM: Gemini API

This matches the current application architecture more closely than an all-in-one Vercel deployment because the backend runs FastAPI with in-process scheduled jobs.

## 2. Root Directories

### Vercel frontend project

- Root Directory: `alphahunter/apps/frontend`
- Install Command: `npm ci`
- Build Command: `npm run build`
- Output Directory: `dist`

The frontend includes `vercel.json` with SPA routing so direct loads and refreshes on routes such as `/history` and `/stock/:symbol` resolve to `index.html` instead of returning `404`.

### Railway backend project

- Root Directory: `alphahunter/apps/backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Keep the Railway backend at a single replica for now because APScheduler runs inside the web process.

## 3. Required Environment Variables

### Backend

```bash
APP_ENV=production
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://*.vercel.app
MINO_API_KEY=your_mino_api_key_here
TINYFISH_RUN_SSE_URL=https://mino.ai/v1/automation/run-sse
LLM_MAX_TOKENS=250
LLM_TIMEOUT_SECS=30
```

Notes:

- `DATABASE_URL` is preferred in hosted environments.
- Local development still falls back to SQLite when `DB_HOST=localhost` and `DB_NAME=alphahunter_dev`.
- `ALLOWED_ORIGINS` supports exact origins and wildcard origins such as `https://*.vercel.app`.

### Frontend

```bash
VITE_API_BASE_URL=https://your-backend.up.railway.app/api
```

For local Vite development, the frontend can use `/api` because `apps/frontend/vite.config.ts` proxies that path to the backend.

## 4. Local Development

### Backend

```bash
cd alphahunter/apps/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd alphahunter/apps/frontend
npm install
npm run dev
```

### Docker Compose

`alphahunter/docker-compose.yml` configures the frontend dev server to proxy `/api` requests to `http://backend:8000` inside Docker.

## 5. Deployment Checklist

### Vercel

- Create a frontend project pointed at `alphahunter/apps/frontend`
- Add `VITE_API_BASE_URL`
- Verify direct loads for `/`, `/history`, `/watchlist`, and `/stock/<symbol>`

### Railway

- Create a backend project pointed at `alphahunter/apps/backend`
- Add `DATABASE_URL`, `REDIS_URL`, `GEMINI_API_KEY`, and `ALLOWED_ORIGINS`
- Verify `GET /api/health`
- Keep the service at one replica

## 6. CI

GitHub Actions runs from `.github/workflows/alphahunter-ci.yml` and currently checks:

- Backend: `pytest -q`
- Frontend: `npm run build`

## 7. Security Notes

- Never commit `.env`
- Do not store the Gemini API key in tracked files
- Rotate any API key that has been pasted into chat or shared outside your secret manager

*Last updated: 2026-03-27*
