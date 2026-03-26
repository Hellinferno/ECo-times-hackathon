# 11 — Environment & DevOps

## AlphaHunter AI — Opportunity & Decision Engine

---

## 1. Overview

This document defines the environment configuration, infrastructure setup, deployment strategy, and operational procedures for AlphaHunter AI across all environments (development, staging, production).

---

## 2. Environment Overview

| Environment | Purpose | Infrastructure | URL |
|-------------|---------|---------------|-----|
| **Development** | Local coding & testing | Docker Compose (laptop) | `localhost:3000` / `localhost:8000` |
| **Staging** | Pre-demo validation | Railway / Render free tier | `staging.alphahunter.ai` |
| **Production** | Live / demo-day deployment | Railway / Render paid tier or AWS EC2 | `app.alphahunter.ai` |

---

## 3. Required Environment Variables

### `.env.example` (full template)

```bash
# ============================================
# ALPHAHUNTER AI — ENVIRONMENT CONFIGURATION
# ============================================

# --- Application ---
APP_ENV=development          # development | staging | production
APP_NAME=AlphaHunter AI
APP_VERSION=1.0.0
LOG_LEVEL=INFO               # DEBUG | INFO | WARNING | ERROR
SECRET_KEY=changeme-use-strong-random-key-in-prod

# --- Database ---
DATABASE_URL=postgresql://alphahunter:password@localhost:5432/alphahunter
# For SQLite (dev only): DATABASE_URL=sqlite:///./alphahunter.db

# --- Redis (Task Queue + Cache) ---
REDIS_URL=redis://localhost:6379/0

# --- Anthropic (LLM) ---
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
LLM_MAX_TOKENS=500
LLM_TIMEOUT_SECS=10

# --- Data Sources ---
YFINANCE_CACHE_TTL_LIVE=300          # seconds: 5 minutes
YFINANCE_CACHE_TTL_HISTORICAL=86400  # seconds: 24 hours
NSE_BULK_DEALS_URL=https://archives.nseindia.com/archives/equities/bhavcopy/pr/PR{date}.zip
NSE_REQUEST_TIMEOUT=15

# --- Scan Configuration ---
SCAN_INTERVAL_MINUTES=15
SCAN_MARKET_HOURS_START=09:15        # IST
SCAN_MARKET_HOURS_END=15:30          # IST
SCAN_PARALLEL_WORKERS=10
SCAN_STOCK_UNIVERSE_SIZE=100

# --- Signal Parameters ---
BREAKOUT_LOOKBACK_DAYS=30
VOLUME_SPIKE_THRESHOLD=2.0
VOLUME_AVG_PERIOD=20
BULK_DEAL_LOOKBACK_DAYS=5

# --- Decision Engine ---
CONFIDENCE_BUY_THRESHOLD=70.0
CONFIDENCE_WATCH_THRESHOLD=50.0
BACKTEST_LOOKBACK_YEARS=2
BACKTEST_OUTCOME_DAYS=5

# --- Alerts ---
DEFAULT_ALERT_CONFIDENCE_THRESHOLD=65.0

# --- CORS ---
ALLOWED_ORIGINS=http://localhost:3000,https://app.alphahunter.ai

# --- Frontend (Vite .env) ---
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## 4. Local Development Setup

### Prerequisites

```bash
# Required
python 3.11+
node 18+
docker + docker-compose
git

# Verify versions
python --version    # Python 3.11.x
node --version      # v18.x.x
docker --version    # Docker 24.x.x
```

### One-Command Setup

```bash
# Clone the repo
git clone https://github.com/your-org/alphahunter.git
cd alphahunter

# Run setup script
bash scripts/dev_setup.sh
```

### `scripts/dev_setup.sh`

```bash
#!/bin/bash
set -e

echo "🚀 AlphaHunter AI — Dev Setup"

# Copy env file
cp .env.example .env
echo "✅ .env created — please add your ANTHROPIC_API_KEY"

# Start infrastructure
docker-compose up -d db redis
echo "✅ PostgreSQL + Redis running"

# Backend setup
cd apps/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "✅ Python dependencies installed"

# Apply database migrations
alembic upgrade head
echo "✅ Database schema applied"

# Seed stock list
python ../../scripts/seed_stocks.py
echo "✅ 100+ NSE stocks seeded"

# Frontend setup
cd ../../apps/frontend
npm install
echo "✅ Node dependencies installed"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start development:"
echo "  Backend:  cd apps/backend && uvicorn main:app --reload --port 8000"
echo "  Frontend: cd apps/frontend && npm run dev"
echo "  Worker:   cd apps/backend && celery -A core.celery_app worker --loglevel=info"
```

### Manual Start (3 terminals)

```bash
# Terminal 1 — Backend API
cd apps/backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2 — Celery Worker
cd apps/backend
source .venv/bin/activate
celery -A core.celery_app worker --loglevel=info --concurrency=5

# Terminal 3 — Frontend
cd apps/frontend
npm run dev
```

---

## 5. Docker Configuration

### `apps/backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `apps/frontend/Dockerfile`

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
ARG VITE_API_BASE_URL
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000
```

### `apps/frontend/nginx.conf`

```nginx
server {
    listen 3000;

    root /usr/share/nginx/html;
    index index.html;

    # Handle React Router paths
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API calls to backend
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 6. Database Management

### Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "add_new_table"

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Backups (Production)

```bash
# Create backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql $DATABASE_URL < backup_20260325_094500.sql
```

### Reset (Development Only)

```bash
# Drop and recreate database
psql -U alphahunter -c "DROP DATABASE alphahunter;"
psql -U alphahunter -c "CREATE DATABASE alphahunter;"
alembic upgrade head
python scripts/seed_stocks.py
```

---

## 7. Deployment — Railway (Recommended for Hackathon)

### Setup Steps

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Add services (from Railway dashboard)
# 1. PostgreSQL plugin
# 2. Redis plugin
# 3. Backend service (point to apps/backend/)
# 4. Frontend service (point to apps/frontend/)

# Set environment variables (Railway dashboard or CLI)
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set APP_ENV=production

# Deploy
railway up
```

### Railway Service Configuration

**Backend Service:**
```
Root Directory: apps/backend
Build Command: pip install -r requirements.txt && alembic upgrade head
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Worker Service:**
```
Root Directory: apps/backend
Start Command: celery -A core.celery_app worker --loglevel=info
```

**Frontend Service:**
```
Root Directory: apps/frontend
Build Command: npm run build
Start Command: serve -s dist -l $PORT
```

---

## 8. Deployment — AWS EC2 (Alternative)

### Minimum Instance: `t3.small` (2 vCPU, 2GB RAM)

```bash
# SSH into instance
ssh -i alphahunter.pem ubuntu@your-ec2-ip

# Install dependencies
sudo apt update && sudo apt install -y docker.io docker-compose nginx certbot

# Clone repo
git clone https://github.com/your-org/alphahunter.git /opt/alphahunter
cd /opt/alphahunter

# Configure environment
cp .env.example .env
nano .env  # Fill in all values

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Check health
curl http://localhost:8000/api/health
```

---

## 9. CI/CD Pipeline

### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: alphahunter_test
          POSTGRES_USER: alphahunter
          POSTGRES_PASSWORD: testpassword
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          cd apps/backend
          pip install -r requirements.txt
      - name: Run migrations
        run: |
          cd apps/backend
          alembic upgrade head
        env:
          DATABASE_URL: postgresql://alphahunter:testpassword@localhost:5432/alphahunter_test
      - name: Run tests
        run: |
          cd apps/backend
          pytest tests/ -v --cov=.
        env:
          DATABASE_URL: postgresql://alphahunter:testpassword@localhost:5432/alphahunter_test
          REDIS_URL: redis://localhost:6379/0
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "18"
      - name: Install + Lint
        run: |
          cd apps/frontend
          npm ci
          npm run lint
          npm run build
```

---

## 10. Monitoring & Logging

### Structured Logging (Backend)

```python
# core/logger.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
            "extra": getattr(record, "extra", {})
        })

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
```

### Health Check Monitoring

```bash
# Simple uptime check (add to cron or Railway healthcheck)
curl -f https://api.alphahunter.ai/api/health || echo "UNHEALTHY"
```

### Log Inspection

```bash
# Docker logs
docker-compose logs -f backend
docker-compose logs -f worker

# Filter errors only
docker-compose logs backend | grep '"level": "ERROR"'
```

---

## 11. Security Checklist

| Item | Status | Notes |
|------|--------|-------|
| `SECRET_KEY` set to random value | Required | Never use default in prod |
| `ANTHROPIC_API_KEY` not in git | Required | Must be in `.env` only |
| CORS restricted to known origins | Required | Set `ALLOWED_ORIGINS` |
| Database not exposed publicly | Required | Only accessible within Docker network |
| Redis not exposed publicly | Required | Same |
| HTTPS on production | Required | Use Railway's auto-SSL or Certbot |
| Rate limiting on scan endpoint | Recommended | Prevent abuse |

---

## 12. Makefile Quick Reference

```bash
make setup          # Full dev environment setup
make dev            # Start all services with docker-compose
make dev-backend    # Start backend only (with hot-reload)
make dev-frontend   # Start frontend only
make test-backend   # Run backend tests
make migrate        # Apply database migrations
make seed           # Seed NSE stock list
make lint           # Run all linters
make logs           # Tail docker-compose logs
make clean          # Stop and remove all containers + volumes
```

---

*Last updated: 2026-03-25 | Version: 1.0*
