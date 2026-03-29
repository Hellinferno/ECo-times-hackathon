<div align="center">

# AlphaHunter AI

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-007ACC?style=flat&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Gemini](https://img.shields.io/badge/Gemini_API-Powered-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-Hackathon-FF6B35?style=flat)](../README.md)

**Autonomous Stock Market Intelligence Engine for Indian Retail Investors**

[How It Works](#how-it-works) · [Quick Start](#quick-start) · [Architecture](#architecture) · [API Reference](#api-endpoints) · [Deployment](#deployment)

</div>

---

## Overview

AlphaHunter continuously monitors **100+ NSE-listed stocks**, detects trading opportunities using a 6-agent AI pipeline, validates every signal against **2 years of historical patterns**, and delivers actionable trade recommendations with specific entry prices, targets, and stop-losses — explained in plain English, grounded in actual market data.

---

## How It Works

```text
Detect → Explain → Validate → Decide → Audit
```

| Step | Agent | What it does |
|------|-------|-------------|
| 1 | **Data Agent** | Fetches live price, volume, and bulk deal data from NSE |
| 2 | **Signal Agent** | Runs 3 detection algorithms: Breakout, Volume Spike, Bulk Deal |
| 3 | **Backtesting Agent** | Matches signal patterns against 2 years of history, measures T+5 outcomes |
| 4 | **Reasoning Agent** | Gemini generates a plain-English explanation referencing actual data values |
| 5 | **Decision Agent** | Scores confidence (0–100), emits BUY / WATCH / AVOID with entry, target, stop-loss |
| 6 | **Audit Agent** | Logs every decision with full provenance for track-record analysis |

The scanner runs automatically every 15 minutes during NSE market hours.

---

## Decision Engine

The confidence score formula:

```text
Confidence = (Signal Score × 0.40) + (Backtest Score × 0.40) + (Signal Count × 0.20)
```

| Confidence | Decision | Meaning |
|------------|----------|---------|
| ≥ 70% | **BUY** | Strong opportunity with validated historical precedent |
| 50–69% | **WATCH** | Potential setup — monitor for confirmation |
| < 50% | **AVOID** | Insufficient evidence to act |

Every BUY/WATCH recommendation includes: entry price, target price, stop-loss, and risk:reward ratio (targeting 1:2.5).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy, APScheduler |
| **Frontend** | React 19, TypeScript, Tailwind CSS 4, Recharts |
| **Database** | PostgreSQL 15, Redis 7 |
| **AI/LLM** | Gemini API (`google-genai`) |
| **Data Sources** | yfinance, NSE bulk deals API, TinyFish |
| **Infrastructure** | Docker Compose, Alembic migrations |

---

## Project Structure

```text
alphahunter/
├── apps/
│   ├── backend/                 # FastAPI application
│   │   ├── agents/              # 6-agent pipeline
│   │   │   ├── data_agent.py
│   │   │   ├── signal_agent.py
│   │   │   ├── backtest_agent.py
│   │   │   ├── reasoning_agent.py
│   │   │   ├── decision_agent.py
│   │   │   └── audit_agent.py
│   │   ├── api/endpoints/       # REST API (14 endpoints)
│   │   ├── models/db/           # SQLAlchemy ORM models (11 tables)
│   │   ├── alembic/             # Database migrations
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings & environment
│   │   └── requirements.txt
│   └── frontend/                # React + TypeScript SPA
│       └── src/
│           ├── api/client.ts    # Typed API client
│           ├── components/      # Navbar, Layout
│           ├── Dashboard.tsx    # Opportunity grid with scan trigger
│           ├── StockDetail.tsx  # Tabbed analysis (Overview, Signals, Backtest, Trade Plan)
│           ├── History.tsx      # Decision history with track record
│           ├── Watchlist.tsx    # Stock watchlist management
│           ├── Alerts.tsx       # Alert center
│           └── Settings.tsx     # System configuration
├── scripts/                     # Seed data scripts
├── docker-compose.yml           # Full stack orchestration
├── .env.example                 # Environment template
└── Makefile                     # Development commands
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/Hellinferno/ECo-times-hackathon.git
cd ECo-times-hackathon/alphahunter

# 2. Start infrastructure
docker compose up -d postgres redis

# 3. Backend
cd apps/backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../../.env.example ../../.env   # fill in GEMINI_API_KEY
python ../../scripts/seed_stocks.py
uvicorn main:app --reload --port 8000

# 4. Frontend (new terminal)
cd apps/frontend
npm install
npm run dev
```

Open <http://localhost:5173> and click **Trigger Market Scan** to start.

---

## Architecture

```text
┌─────────────┐     ┌──────────────────────────────────────────────┐
│   React UI  │────▶│               FastAPI Backend                 │
│  Port 5173  │◀────│               Port 8000                       │
└─────────────┘     │                                              │
                    │  ┌──────┐  ┌────────┐  ┌────────────┐       │
                    │  │ Data │─▶│ Signal │─▶│ Backtesting│       │
                    │  │Agent │  │ Agent  │  │ Agent      │       │
                    │  └──────┘  └────────┘  └────────────┘       │
                    │                │              │              │
                    │         ┌──────▼────┐  ┌─────▼──────┐       │
                    │         │ Reasoning │  │  Decision  │       │
                    │         │ Agent     │  │  Agent     │       │
                    │         └───────────┘  └────────────┘       │
                    │                              │               │
                    │                       ┌──────▼──────┐        │
                    │                       │  Audit      │        │
                    │                       │  Agent      │        │
                    │                       └─────────────┘        │
                    └──────────────────────────────────────────────┘
                          │                       │
                    ┌─────▼──────┐          ┌─────▼─────┐
                    │ PostgreSQL │          │   Redis   │
                    │   :5432   │          │   :6379   │
                    └────────────┘          └───────────┘
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/scan` | Trigger a full market scan |
| `GET` | `/api/opportunities` | List active opportunities |
| `GET` | `/api/opportunities/:id` | Opportunity detail |
| `GET` | `/api/stock/:symbol` | Full stock analysis |
| `GET` | `/api/history` | Decision history with track record |
| `GET` | `/api/history/scans` | Scan run history |
| `GET` | `/api/watchlist` | User watchlist |
| `POST` | `/api/watchlist/:symbol` | Add to watchlist |
| `DELETE` | `/api/watchlist/:symbol` | Remove from watchlist |
| `GET` | `/api/alerts` | List alerts |
| `POST` | `/api/alerts/mark-read` | Mark alerts as read |
| `GET` | `/api/settings` | System settings |
| `PATCH` | `/api/settings` | Update settings |
| `GET` | `/api/health` | Health check |

---

## Environment Variables

```env
# Required
GEMINI_API_KEY=your_google_ai_key
GEMINI_MODEL=gemini-2.5-flash

# Database (auto-configured by Docker Compose)
DATABASE_URL=postgresql://alphahunter:alphahunter@localhost:5432/alphahunter
REDIS_URL=redis://localhost:6379/0

# CORS
ALLOWED_ORIGINS=http://localhost:5173,https://<your-vercel-domain>

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## Deployment

**Recommended: split frontend/backend deployment**

### Frontend → Vercel

- Root Directory: `alphahunter/apps/frontend`
- The included `vercel.json` rewrites all routes to `index.html` for React Router
- Set `VITE_API_BASE_URL=https://<your-railway-backend>/api` in Vercel environment variables

### Backend → Railway

- Root Directory: `alphahunter/apps/backend`
- Set `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-2.5-flash`
- Set `ALLOWED_ORIGINS=https://<your-vercel-domain>,https://*.vercel.app`
- Keep at **single replica** — APScheduler runs in-process

---

## Project Documentation

Comprehensive specifications in [`../files/`](../files/):

| # | Document | Contents |
|---|----------|----------|
| 01 | Project Overview | Vision, pipeline, tech stack, demo flow |
| 02 | User Stories | 23 stories across 8 epics with acceptance criteria |
| 03 | Information Architecture | Navigation, pages, content models, user flows |
| 04 | System Architecture | 7-agent pipeline, data flow, failure handling |
| 05 | Database Schema | 10 tables, DDL, indexes, views, migration strategy |
| 06 | API Contracts | Full REST specification with request/response schemas |
| 07 | Monorepo Structure | Folder layout, Docker config, naming conventions |
| 08 | Computation Engine | Mathematical formulas for all signal detection algorithms |
| 09 | Engineering Scope | MVP boundaries, constraints, risk register |
| 10 | Development Phases | Hour-by-hour hackathon build plan |
| 11 | Environment & DevOps | Setup, deployment, CI/CD, monitoring |
| 12 | Testing Strategy | Test types, fixtures, 30+ test case specifications |

---

← [Back to suite overview](../README.md)
