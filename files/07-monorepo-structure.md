# 07 — Monorepo Structure

## AlphaHunter AI — Opportunity & Decision Engine

---

## 1. Overview

AlphaHunter AI uses a **monorepo** structure with separate packages for the backend engine, frontend dashboard, and shared utilities. This keeps all code in one repository while maintaining clean separation of concerns.

---

## 2. Repository Root Structure

```
alphahunter/
├── .github/
│   └── workflows/
│       ├── ci.yml                  # CI pipeline (lint, test, build)
│       └── deploy.yml              # CD pipeline (staging, prod)
│
├── apps/
│   ├── backend/                    # Python FastAPI backend
│   └── frontend/                   # React + TypeScript frontend
│
├── packages/
│   └── shared/                     # Shared types, constants (future)
│
├── scripts/
│   ├── seed_stocks.py              # Seed NSE stock list into DB
│   ├── backfill_decisions.py       # Measure outcomes for past decisions
│   └── dev_setup.sh                # One-command dev environment setup
│
├── docker-compose.yml              # Local dev environment
├── docker-compose.prod.yml         # Production compose
├── .env.example                    # Environment variable template
├── .gitignore
├── README.md
└── Makefile                        # Dev task shortcuts
```

---

## 3. Backend Structure — `apps/backend/`

```
apps/backend/
├── main.py                         # FastAPI app entry point
├── config.py                       # Settings / environment config
├── requirements.txt                # Python dependencies
├── Dockerfile
├── alembic.ini                     # Database migration config
│
├── alembic/
│   ├── env.py
│   └── versions/
│       ├── 001_initial_schema.py
│       ├── 002_add_bulk_deals.py
│       └── 003_add_audit_logs.py
│
├── api/
│   ├── __init__.py
│   ├── router.py                   # Top-level router (mounts all sub-routers)
│   └── endpoints/
│       ├── __init__.py
│       ├── scan.py                 # POST /scan, GET /scan/{id}/status
│       ├── opportunities.py        # GET /opportunities
│       ├── stock.py                # GET /stock/{symbol}, /chart
│       ├── history.py              # GET /history, /{id}, /export
│       ├── watchlist.py            # GET/POST/DELETE /watchlist
│       ├── alerts.py               # GET /alerts, POST /alerts/mark-read
│       ├── settings.py             # GET/PATCH /settings
│       └── health.py               # GET /health
│
├── agents/
│   ├── __init__.py
│   ├── scheduler_agent.py          # Scan scheduling & orchestration
│   ├── data_agent.py               # Market data fetching & caching
│   ├── signal_agent.py             # Technical + fundamental signal detection
│   ├── reasoning_agent.py          # LLM explanation generation
│   ├── backtesting_agent.py        # Historical signal validation
│   ├── decision_agent.py           # Final decision + trade parameters
│   └── audit_agent.py             # Decision logging & outcome tracking
│
├── models/
│   ├── __init__.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                 # SQLAlchemy Base
│   │   ├── stock.py                # Stock ORM model
│   │   ├── scan_run.py             # ScanRun ORM model
│   │   ├── scan_result.py          # ScanResult ORM model
│   │   ├── decision.py             # Decision ORM model
│   │   ├── bulk_deal.py            # BulkDeal ORM model
│   │   ├── watchlist_item.py       # WatchlistItem ORM model
│   │   ├── alert.py                # Alert ORM model
│   │   ├── market_data_cache.py    # MarketDataCache ORM model
│   │   └── system_setting.py      # SystemSetting ORM model
│   │
│   └── schemas/
│       ├── __init__.py
│       ├── scan.py                 # Pydantic schemas for scan endpoints
│       ├── opportunity.py          # Pydantic schemas for opportunity data
│       ├── stock.py                # Pydantic schemas for stock detail
│       ├── decision.py             # Pydantic schemas for decisions
│       ├── watchlist.py            # Pydantic schemas for watchlist
│       ├── alert.py                # Pydantic schemas for alerts
│       └── common.py              # Shared schemas (APIResponse, Meta, etc.)
│
├── services/
│   ├── __init__.py
│   ├── scan_service.py             # Business logic layer for scan operations
│   ├── stock_service.py            # Business logic for stock detail
│   ├── history_service.py          # Business logic for decision history
│   ├── watchlist_service.py        # Business logic for watchlist
│   └── alert_service.py           # Business logic for alerts
│
├── data_sources/
│   ├── __init__.py
│   ├── yfinance_client.py          # yfinance wrapper with error handling
│   ├── nse_client.py               # NSE bulk deals + corporate data
│   └── cache_client.py            # Redis cache wrapper
│
├── core/
│   ├── __init__.py
│   ├── database.py                 # DB session factory
│   ├── redis.py                    # Redis client singleton
│   ├── celery_app.py               # Celery app instance
│   ├── logger.py                   # Structured logging setup
│   └── exceptions.py              # Custom exception classes
│
├── tasks/
│   ├── __init__.py
│   ├── scan_task.py                # Celery task: run full scan
│   └── outcome_task.py            # Celery task: measure T+5 outcomes
│
└── tests/
    ├── __init__.py
    ├── conftest.py                 # Test fixtures
    ├── unit/
    │   ├── test_signal_agent.py
    │   ├── test_backtesting_agent.py
    │   ├── test_decision_agent.py
    │   └── test_reasoning_agent.py
    └── integration/
        ├── test_scan_api.py
        ├── test_stock_api.py
        └── test_history_api.py
```

---

## 4. Frontend Structure — `apps/frontend/`

```
apps/frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── Dockerfile
│
├── public/
│   └── favicon.ico
│
├── src/
│   ├── main.tsx                    # React entry point
│   ├── App.tsx                     # Root component + routing
│   │
│   ├── pages/
│   │   ├── Dashboard.tsx           # Home / market pulse
│   │   ├── Scanner.tsx             # Scan trigger + opportunity list
│   │   ├── StockDetail.tsx         # Full stock analysis page
│   │   ├── History.tsx             # Past decisions log
│   │   ├── Watchlist.tsx           # User watchlist
│   │   ├── Alerts.tsx              # Notification center
│   │   └── Settings.tsx           # User preferences
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopBar.tsx
│   │   │   └── PageWrapper.tsx
│   │   │
│   │   ├── scanner/
│   │   │   ├── OpportunityCard.tsx  # Card for each opportunity
│   │   │   ├── ScanButton.tsx       # Trigger + loading state
│   │   │   ├── FilterBar.tsx        # Action + signal filters
│   │   │   └── ScanStats.tsx        # Stocks scanned, signals found
│   │   │
│   │   ├── stock/
│   │   │   ├── StockTabs.tsx        # Tab container
│   │   │   ├── OverviewTab.tsx
│   │   │   ├── SignalsTab.tsx
│   │   │   ├── BacktestTab.tsx
│   │   │   ├── TradePlanTab.tsx
│   │   │   ├── ChartTab.tsx
│   │   │   ├── SignalCard.tsx        # Individual signal display
│   │   │   ├── ReasoningBox.tsx     # LLM explanation display
│   │   │   └── DecisionCard.tsx     # BUY/WATCH/AVOID card
│   │   │
│   │   ├── history/
│   │   │   ├── DecisionTable.tsx
│   │   │   ├── DecisionRow.tsx
│   │   │   ├── DecisionDetail.tsx   # Full replay modal
│   │   │   ├── TrackRecordStats.tsx # Win rate summary
│   │   │   └── ExportButton.tsx
│   │   │
│   │   ├── charts/
│   │   │   ├── PriceChart.tsx       # Candlestick / line chart
│   │   │   ├── VolumeChart.tsx
│   │   │   ├── BacktestChart.tsx    # Past signal markers
│   │   │   └── ConfidenceGauge.tsx  # Visual confidence meter
│   │   │
│   │   └── common/
│   │       ├── ActionBadge.tsx      # BUY/WATCH/AVOID badge
│   │       ├── ConfidencePill.tsx   # % pill
│   │       ├── LoadingSpinner.tsx
│   │       ├── EmptyState.tsx
│   │       ├── ErrorState.tsx
│   │       └── Tooltip.tsx
│   │
│   ├── hooks/
│   │   ├── useScan.ts               # Scan trigger + polling
│   │   ├── useOpportunities.ts      # Fetch + filter opportunities
│   │   ├── useStockDetail.ts        # Stock analysis data
│   │   ├── useHistory.ts            # Decision history
│   │   ├── useWatchlist.ts          # Watchlist CRUD
│   │   └── useAlerts.ts            # Alerts + unread count
│   │
│   ├── store/
│   │   ├── scanStore.ts             # Zustand: scan state
│   │   ├── filterStore.ts           # Zustand: active filters
│   │   └── settingsStore.ts        # Zustand: user preferences
│   │
│   ├── api/
│   │   ├── client.ts               # Axios instance + interceptors
│   │   ├── scan.api.ts
│   │   ├── opportunities.api.ts
│   │   ├── stock.api.ts
│   │   ├── history.api.ts
│   │   ├── watchlist.api.ts
│   │   ├── alerts.api.ts
│   │   └── settings.api.ts
│   │
│   ├── types/
│   │   ├── opportunity.ts
│   │   ├── stock.ts
│   │   ├── decision.ts
│   │   ├── signal.ts
│   │   └── common.ts
│   │
│   └── utils/
│       ├── formatters.ts            # Currency, %, date formatters
│       ├── colors.ts                # Action → color mappings
│       └── constants.ts            # App-wide constants
│
└── tests/
    └── components/
        ├── OpportunityCard.test.tsx
        └── DecisionCard.test.tsx
```

---

## 5. Key Configuration Files

### `docker-compose.yml`

```yaml
version: "3.9"

services:
  backend:
    build: ./apps/backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://alphahunter:password@db:5432/alphahunter
      - REDIS_URL=redis://redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - db
      - redis

  worker:
    build: ./apps/backend
    command: celery -A core.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://alphahunter:password@db:5432/alphahunter
      - REDIS_URL=redis://redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - db
      - redis

  frontend:
    build: ./apps/frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000/api

  db:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=alphahunter
      - POSTGRES_USER=alphahunter
      - POSTGRES_PASSWORD=password
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

---

### `.env.example`

```
# Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database
DATABASE_URL=postgresql://alphahunter:password@localhost:5432/alphahunter

# Redis
REDIS_URL=redis://localhost:6379/0

# Application
APP_ENV=development
LOG_LEVEL=INFO
SCAN_INTERVAL_MINUTES=15
```

---

### `Makefile`

```makefile
setup:
	cp .env.example .env
	docker-compose up -d db redis
	cd apps/backend && pip install -r requirements.txt
	cd apps/backend && alembic upgrade head
	cd apps/backend && python ../../scripts/seed_stocks.py

dev-backend:
	cd apps/backend && uvicorn main:app --reload --port 8000

dev-frontend:
	cd apps/frontend && npm run dev

dev:
	docker-compose up

test-backend:
	cd apps/backend && pytest tests/ -v

test-frontend:
	cd apps/frontend && npm test

lint:
	cd apps/backend && flake8 . && black --check .
	cd apps/frontend && npm run lint

migrate:
	cd apps/backend && alembic upgrade head

seed:
	python scripts/seed_stocks.py
```

---

## 6. Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Python files | `snake_case` | `signal_agent.py` |
| Python classes | `PascalCase` | `SignalAgent` |
| Python functions | `snake_case` | `detect_breakout()` |
| React files | `PascalCase` | `OpportunityCard.tsx` |
| React components | `PascalCase` | `OpportunityCard` |
| TypeScript types | `PascalCase` | `OpportunityData` |
| Hooks | `camelCase` with `use` prefix | `useScan` |
| API files | `camelCase.api.ts` | `scan.api.ts` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_CONFIDENCE_THRESHOLD` |

---

*Last updated: 2026-03-25 | Version: 1.0*
