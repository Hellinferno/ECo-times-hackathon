# 07 â€” Monorepo Structure

## AlphaHunter AI â€” Opportunity & Decision Engine

---

## 1. Overview

AlphaHunter AI uses a **monorepo** structure with separate packages for the backend engine, frontend dashboard, and shared utilities. This keeps all code in one repository while maintaining clean separation of concerns.

---

## 2. Repository Root Structure

```
alphahunter/
â”œâ”€â”€ .github/
â”‚   â””â”€â”€ workflows/
â”‚       â”œâ”€â”€ ci.yml                  # CI pipeline (lint, test, build)
â”‚       â””â”€â”€ deploy.yml              # CD pipeline (staging, prod)
â”‚
â”œâ”€â”€ apps/
â”‚   â”œâ”€â”€ backend/                    # Python FastAPI backend
â”‚   â””â”€â”€ frontend/                   # React + TypeScript frontend
â”‚
â”œâ”€â”€ packages/
â”‚   â””â”€â”€ shared/                     # Shared types, constants (future)
â”‚
â”œâ”€â”€ scripts/
â”‚   â”œâ”€â”€ seed_stocks.py              # Seed NSE stock list into DB
â”‚   â”œâ”€â”€ backfill_decisions.py       # Measure outcomes for past decisions
â”‚   â””â”€â”€ dev_setup.sh                # One-command dev environment setup
â”‚
â”œâ”€â”€ docker-compose.yml              # Local dev environment
â”œâ”€â”€ docker-compose.prod.yml         # Production compose
â”œâ”€â”€ .env.example                    # Environment variable template
â”œâ”€â”€ .gitignore
â”œâ”€â”€ README.md
â””â”€â”€ Makefile                        # Dev task shortcuts
```

---

## 3. Backend Structure â€” `apps/backend/`

```
apps/backend/
â”œâ”€â”€ main.py                         # FastAPI app entry point
â”œâ”€â”€ config.py                       # Settings / environment config
â”œâ”€â”€ requirements.txt                # Python dependencies
â”œâ”€â”€ Dockerfile
â”œâ”€â”€ alembic.ini                     # Database migration config
â”‚
â”œâ”€â”€ alembic/
â”‚   â”œâ”€â”€ env.py
â”‚   â””â”€â”€ versions/
â”‚       â”œâ”€â”€ 001_initial_schema.py
â”‚       â”œâ”€â”€ 002_add_bulk_deals.py
â”‚       â””â”€â”€ 003_add_audit_logs.py
â”‚
â”œâ”€â”€ api/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ router.py                   # Top-level router (mounts all sub-routers)
â”‚   â””â”€â”€ endpoints/
â”‚       â”œâ”€â”€ __init__.py
â”‚       â”œâ”€â”€ scan.py                 # POST /scan, GET /scan/{id}/status
â”‚       â”œâ”€â”€ opportunities.py        # GET /opportunities
â”‚       â”œâ”€â”€ stock.py                # GET /stock/{symbol}, /chart
â”‚       â”œâ”€â”€ history.py              # GET /history, /{id}, /export
â”‚       â”œâ”€â”€ watchlist.py            # GET/POST/DELETE /watchlist
â”‚       â”œâ”€â”€ alerts.py               # GET /alerts, POST /alerts/mark-read
â”‚       â”œâ”€â”€ settings.py             # GET/PATCH /settings
â”‚       â””â”€â”€ health.py               # GET /health
â”‚
â”œâ”€â”€ agents/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ scheduler_agent.py          # Scan scheduling & orchestration
â”‚   â”œâ”€â”€ data_agent.py               # Market data fetching & caching
â”‚   â”œâ”€â”€ signal_agent.py             # Technical + fundamental signal detection
â”‚   â”œâ”€â”€ reasoning_agent.py          # LLM explanation generation
â”‚   â”œâ”€â”€ backtesting_agent.py        # Historical signal validation
â”‚   â”œâ”€â”€ decision_agent.py           # Final decision + trade parameters
â”‚   â””â”€â”€ audit_agent.py             # Decision logging & outcome tracking
â”‚
â”œâ”€â”€ models/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ db/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ base.py                 # SQLAlchemy Base
â”‚   â”‚   â”œâ”€â”€ stock.py                # Stock ORM model
â”‚   â”‚   â”œâ”€â”€ scan_run.py             # ScanRun ORM model
â”‚   â”‚   â”œâ”€â”€ scan_result.py          # ScanResult ORM model
â”‚   â”‚   â”œâ”€â”€ decision.py             # Decision ORM model
â”‚   â”‚   â”œâ”€â”€ bulk_deal.py            # BulkDeal ORM model
â”‚   â”‚   â”œâ”€â”€ watchlist_item.py       # WatchlistItem ORM model
â”‚   â”‚   â”œâ”€â”€ alert.py                # Alert ORM model
â”‚   â”‚   â”œâ”€â”€ market_data_cache.py    # MarketDataCache ORM model
â”‚   â”‚   â””â”€â”€ system_setting.py      # SystemSetting ORM model
â”‚   â”‚
â”‚   â””â”€â”€ schemas/
â”‚       â”œâ”€â”€ __init__.py
â”‚       â”œâ”€â”€ scan.py                 # Pydantic schemas for scan endpoints
â”‚       â”œâ”€â”€ opportunity.py          # Pydantic schemas for opportunity data
â”‚       â”œâ”€â”€ stock.py                # Pydantic schemas for stock detail
â”‚       â”œâ”€â”€ decision.py             # Pydantic schemas for decisions
â”‚       â”œâ”€â”€ watchlist.py            # Pydantic schemas for watchlist
â”‚       â”œâ”€â”€ alert.py                # Pydantic schemas for alerts
â”‚       â””â”€â”€ common.py              # Shared schemas (APIResponse, Meta, etc.)
â”‚
â”œâ”€â”€ services/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ scan_service.py             # Business logic layer for scan operations
â”‚   â”œâ”€â”€ stock_service.py            # Business logic for stock detail
â”‚   â”œâ”€â”€ history_service.py          # Business logic for decision history
â”‚   â”œâ”€â”€ watchlist_service.py        # Business logic for watchlist
â”‚   â””â”€â”€ alert_service.py           # Business logic for alerts
â”‚
â”œâ”€â”€ data_sources/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ yfinance_client.py          # yfinance wrapper with error handling
â”‚   â”œâ”€â”€ nse_client.py               # NSE bulk deals + corporate data
â”‚   â””â”€â”€ cache_client.py            # Redis cache wrapper
â”‚
â”œâ”€â”€ core/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ database.py                 # DB session factory
â”‚   â”œâ”€â”€ redis.py                    # Redis client singleton
â”‚   â”œâ”€â”€ celery_app.py               # Celery app instance
â”‚   â”œâ”€â”€ logger.py                   # Structured logging setup
â”‚   â””â”€â”€ exceptions.py              # Custom exception classes
â”‚
â”œâ”€â”€ tasks/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ scan_task.py                # Celery task: run full scan
â”‚   â””â”€â”€ outcome_task.py            # Celery task: measure T+5 outcomes
â”‚
â””â”€â”€ tests/
    â”œâ”€â”€ __init__.py
    â”œâ”€â”€ conftest.py                 # Test fixtures
    â”œâ”€â”€ unit/
    â”‚   â”œâ”€â”€ test_signal_agent.py
    â”‚   â”œâ”€â”€ test_backtesting_agent.py
    â”‚   â”œâ”€â”€ test_decision_agent.py
    â”‚   â””â”€â”€ test_reasoning_agent.py
    â””â”€â”€ integration/
        â”œâ”€â”€ test_scan_api.py
        â”œâ”€â”€ test_stock_api.py
        â””â”€â”€ test_history_api.py
```

---

## 4. Frontend Structure â€” `apps/frontend/`

```
apps/frontend/
â”œâ”€â”€ index.html
â”œâ”€â”€ package.json
â”œâ”€â”€ tsconfig.json
â”œâ”€â”€ vite.config.ts
â”œâ”€â”€ tailwind.config.js
â”œâ”€â”€ Dockerfile
â”‚
â”œâ”€â”€ public/
â”‚   â””â”€â”€ favicon.ico
â”‚
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ main.tsx                    # React entry point
â”‚   â”œâ”€â”€ App.tsx                     # Root component + routing
â”‚   â”‚
â”‚   â”œâ”€â”€ pages/
â”‚   â”‚   â”œâ”€â”€ Dashboard.tsx           # Home / market pulse
â”‚   â”‚   â”œâ”€â”€ Scanner.tsx             # Scan trigger + opportunity list
â”‚   â”‚   â”œâ”€â”€ StockDetail.tsx         # Full stock analysis page
â”‚   â”‚   â”œâ”€â”€ History.tsx             # Past decisions log
â”‚   â”‚   â”œâ”€â”€ Watchlist.tsx           # User watchlist
â”‚   â”‚   â”œâ”€â”€ Alerts.tsx              # Notification center
â”‚   â”‚   â””â”€â”€ Settings.tsx           # User preferences
â”‚   â”‚
â”‚   â”œâ”€â”€ components/
â”‚   â”‚   â”œâ”€â”€ layout/
â”‚   â”‚   â”‚   â”œâ”€â”€ Sidebar.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ TopBar.tsx
â”‚   â”‚   â”‚   â””â”€â”€ PageWrapper.tsx
â”‚   â”‚   â”‚
â”‚   â”‚   â”œâ”€â”€ scanner/
â”‚   â”‚   â”‚   â”œâ”€â”€ OpportunityCard.tsx  # Card for each opportunity
â”‚   â”‚   â”‚   â”œâ”€â”€ ScanButton.tsx       # Trigger + loading state
â”‚   â”‚   â”‚   â”œâ”€â”€ FilterBar.tsx        # Action + signal filters
â”‚   â”‚   â”‚   â””â”€â”€ ScanStats.tsx        # Stocks scanned, signals found
â”‚   â”‚   â”‚
â”‚   â”‚   â”œâ”€â”€ stock/
â”‚   â”‚   â”‚   â”œâ”€â”€ StockTabs.tsx        # Tab container
â”‚   â”‚   â”‚   â”œâ”€â”€ OverviewTab.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ SignalsTab.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ BacktestTab.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ TradePlanTab.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ ChartTab.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ SignalCard.tsx        # Individual signal display
â”‚   â”‚   â”‚   â”œâ”€â”€ ReasoningBox.tsx     # LLM explanation display
â”‚   â”‚   â”‚   â””â”€â”€ DecisionCard.tsx     # BUY/WATCH/AVOID card
â”‚   â”‚   â”‚
â”‚   â”‚   â”œâ”€â”€ history/
â”‚   â”‚   â”‚   â”œâ”€â”€ DecisionTable.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ DecisionRow.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ DecisionDetail.tsx   # Full replay modal
â”‚   â”‚   â”‚   â”œâ”€â”€ TrackRecordStats.tsx # Win rate summary
â”‚   â”‚   â”‚   â””â”€â”€ ExportButton.tsx
â”‚   â”‚   â”‚
â”‚   â”‚   â”œâ”€â”€ charts/
â”‚   â”‚   â”‚   â”œâ”€â”€ PriceChart.tsx       # Candlestick / line chart
â”‚   â”‚   â”‚   â”œâ”€â”€ VolumeChart.tsx
â”‚   â”‚   â”‚   â”œâ”€â”€ BacktestChart.tsx    # Past signal markers
â”‚   â”‚   â”‚   â””â”€â”€ ConfidenceGauge.tsx  # Visual confidence meter
â”‚   â”‚   â”‚
â”‚   â”‚   â””â”€â”€ common/
â”‚   â”‚       â”œâ”€â”€ ActionBadge.tsx      # BUY/WATCH/AVOID badge
â”‚   â”‚       â”œâ”€â”€ ConfidencePill.tsx   # % pill
â”‚   â”‚       â”œâ”€â”€ LoadingSpinner.tsx
â”‚   â”‚       â”œâ”€â”€ EmptyState.tsx
â”‚   â”‚       â”œâ”€â”€ ErrorState.tsx
â”‚   â”‚       â””â”€â”€ Tooltip.tsx
â”‚   â”‚
â”‚   â”œâ”€â”€ hooks/
â”‚   â”‚   â”œâ”€â”€ useScan.ts               # Scan trigger + polling
â”‚   â”‚   â”œâ”€â”€ useOpportunities.ts      # Fetch + filter opportunities
â”‚   â”‚   â”œâ”€â”€ useStockDetail.ts        # Stock analysis data
â”‚   â”‚   â”œâ”€â”€ useHistory.ts            # Decision history
â”‚   â”‚   â”œâ”€â”€ useWatchlist.ts          # Watchlist CRUD
â”‚   â”‚   â””â”€â”€ useAlerts.ts            # Alerts + unread count
â”‚   â”‚
â”‚   â”œâ”€â”€ store/
â”‚   â”‚   â”œâ”€â”€ scanStore.ts             # Zustand: scan state
â”‚   â”‚   â”œâ”€â”€ filterStore.ts           # Zustand: active filters
â”‚   â”‚   â””â”€â”€ settingsStore.ts        # Zustand: user preferences
â”‚   â”‚
â”‚   â”œâ”€â”€ api/
â”‚   â”‚   â”œâ”€â”€ client.ts               # Axios instance + interceptors
â”‚   â”‚   â”œâ”€â”€ scan.api.ts
â”‚   â”‚   â”œâ”€â”€ opportunities.api.ts
â”‚   â”‚   â”œâ”€â”€ stock.api.ts
â”‚   â”‚   â”œâ”€â”€ history.api.ts
â”‚   â”‚   â”œâ”€â”€ watchlist.api.ts
â”‚   â”‚   â”œâ”€â”€ alerts.api.ts
â”‚   â”‚   â””â”€â”€ settings.api.ts
â”‚   â”‚
â”‚   â”œâ”€â”€ types/
â”‚   â”‚   â”œâ”€â”€ opportunity.ts
â”‚   â”‚   â”œâ”€â”€ stock.ts
â”‚   â”‚   â”œâ”€â”€ decision.ts
â”‚   â”‚   â”œâ”€â”€ signal.ts
â”‚   â”‚   â””â”€â”€ common.ts
â”‚   â”‚
â”‚   â””â”€â”€ utils/
â”‚       â”œâ”€â”€ formatters.ts            # Currency, %, date formatters
â”‚       â”œâ”€â”€ colors.ts                # Action â†’ color mappings
â”‚       â””â”€â”€ constants.ts            # App-wide constants
â”‚
â””â”€â”€ tests/
    â””â”€â”€ components/
        â”œâ”€â”€ OpportunityCard.test.tsx
        â””â”€â”€ DecisionCard.test.tsx
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
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - db
      - redis

  worker:
    build: ./apps/backend
    command: celery -A core.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://alphahunter:password@db:5432/alphahunter
      - REDIS_URL=redis://redis:6379/0
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - db
      - redis

  frontend:
    build: ./apps/frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_BASE_URL=/api

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
# Gemini
GEMINI_API_KEY=your_gemini_api_key_here

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
