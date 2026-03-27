# AlphaHunter AI

**Autonomous Stock Market Intelligence Engine for Indian Retail Investors**

AlphaHunter AI continuously monitors 100+ NSE-listed stocks, detects trading opportunities using multi-signal analysis, explains reasoning in plain English backed by real data, validates recommendations against 2 years of historical patterns, and delivers actionable trade recommendations with specific entry prices, targets, and stop-losses.

---

## How It Works

```
Detect → Explain → Validate → Decide → Audit
```

1. **Market Scanner** — Monitors NSE stocks every 15 minutes during market hours
2. **Signal Detection** — 3 algorithms: Breakout, Volume Spike, Bulk Deal detection
3. **AI Reasoning** — Gemini generates data-grounded explanations referencing actual values
4. **Backtesting** — Historical pattern matching with T+5 outcome measurement
5. **Decision Engine** — Outputs BUY/WATCH/AVOID with 0-100 confidence score, entry, target, stop-loss

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy, APScheduler |
| **Frontend** | React 19, TypeScript, Tailwind CSS 4, Recharts |
| **Database** | PostgreSQL 15, Redis 7 |
| **AI/LLM** | Gemini API (`google-genai`) |
| **Data** | yfinance, NSE bulk deals API |
| **Infra** | Docker Compose, Alembic migrations |

---

## Project Structure

```
alphahunter/
├── apps/
│   ├── backend/                 # FastAPI application
│   │   ├── agents/              # 6-agent pipeline (Data, Signal, Backtest, Reasoning, Decision, Audit)
│   │   ├── api/endpoints/       # REST API (14 endpoints)
│   │   ├── models/db/           # SQLAlchemy ORM models (11 tables)
│   │   ├── alembic/             # Database migrations
│   │   ├── main.py              # FastAPI app entry point
│   │   └── config.py            # Settings & environment
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
├── files/                       # Project specifications & architecture docs
├── docker-compose.yml           # Full stack orchestration
└── Makefile                     # Development commands
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/scan` | Trigger full market scan |
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

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (for PostgreSQL & Redis)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/Hellinferno/ECo-times-hackathon.git
cd ECo-times-hackathon

# 2. Start infrastructure
cd alphahunter
docker compose up -d postgres redis

# 3. Backend setup
cd apps/backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../../.env.example ../../.env # Edit .env with your Gemini and data-provider keys
python -c "from database import engine; from models.db import Base; Base.metadata.create_all(bind=engine)"
python ../../scripts/seed_stocks.py
uvicorn main:app --reload --port 8000

# 4. Frontend setup (new terminal)
cd apps/frontend
npm install
npm run dev
```

Open http://localhost:5173 and click **Trigger Market Scan** to start.

---

## Deployment

**Recommended split deployment**

- **Frontend (Vercel)** Root Directory: `alphahunter/apps/frontend`
- **Backend (Railway)** Root Directory: `alphahunter/apps/backend`

### Vercel

- The frontend includes `alphahunter/apps/frontend/vercel.json` so React Router paths rewrite to `index.html` instead of returning `404`.
- Set `VITE_API_BASE_URL=https://<your-railway-backend>/api` in the Vercel project environment variables.

### Railway

- Set `GEMINI_API_KEY` and optionally `GEMINI_MODEL=gemini-2.5-flash`.
- Set `ALLOWED_ORIGINS=https://<your-vercel-domain>,https://*.vercel.app`.
- Keep the backend service at a single replica for now because APScheduler runs in-process.

---

## Decision Engine

The confidence score is calculated as:

```
Confidence = (Signal Score x 0.40) + (Backtest Score x 0.40) + (Signal Count x 0.20)
```

| Confidence | Action | Meaning |
|-----------|--------|---------|
| >= 70% | **BUY** | Strong opportunity with validated history |
| 50-69% | **WATCH** | Potential — monitor for confirmation |
| < 50% | **AVOID** | Insufficient evidence |

Each BUY/WATCH recommendation includes: entry price, target price, stop-loss, and risk:reward ratio (targeting 1:2.5).

---

## Architecture

```
┌─────────────┐     ┌─────────────────────────────────────────────┐
│   React UI  │────▶│              FastAPI Backend                 │
│  Port 5173  │◀────│              Port 8000                       │
└─────────────┘     │                                             │
                    │  ┌─────┐  ┌────────┐  ┌───────────┐        │
                    │  │Data │─▶│Signal  │─▶│Backtesting│        │
                    │  │Agent│  │Agent   │  │Agent      │        │
                    │  └─────┘  └────────┘  └───────────┘        │
                    │              │              │                │
                    │         ┌────▼────┐  ┌─────▼─────┐         │
                    │         │Reasoning│  │ Decision  │         │
                    │         │Agent    │  │ Agent     │         │
                    │         └─────────┘  └───────────┘         │
                    │                           │                 │
                    │                     ┌─────▼─────┐          │
                    │                     │  Audit    │          │
                    │                     │  Agent    │          │
                    │                     └───────────┘          │
                    └─────────────────────────────────────────────┘
                         │                      │
                    ┌────▼────┐           ┌─────▼─────┐
                    │PostgreSQL│           │  Redis    │
                    │  :5432  │           │  :6379    │
                    └─────────┘           └───────────┘
```

---

## Documentation

Comprehensive project specifications are in the [`files/`](files/) directory:

| # | Document | Description |
|---|----------|-------------|
| 01 | Project Overview | Vision, pipeline, tech stack, demo flow |
| 02 | User Stories | 23 stories across 8 epics with acceptance criteria |
| 03 | Information Architecture | Navigation, pages, content models, user flows |
| 04 | System Architecture | 7-agent pipeline, data flow, failure handling |
| 05 | Database Schema | 10 tables, DDL, indexes, views, migration strategy |
| 06 | API Contracts | Full REST specification with request/response schemas |
| 07 | Monorepo Structure | Folder layout, Docker config, naming conventions |
| 08 | Computation Engine | Mathematical formulas for all signal detection |
| 09 | Engineering Scope | MVP boundaries, constraints, risk register |
| 10 | Development Phases | Hour-by-hour hackathon build plan |
| 11 | Environment & DevOps | Setup, deployment, CI/CD, monitoring |
| 12 | Testing Strategy | Test types, fixtures, 30+ test case specifications |

---

## License

Built for the ECo Times Hackathon.
