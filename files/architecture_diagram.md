# Architecture Diagram

## AlphaHunter AI — System Architecture Overview

---

## 1. Full System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ALPHAHUNTER AI SYSTEM                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         FRONTEND (React)                         │   │
│  │  Dashboard │ Scanner │ Stock Detail │ History │ Watchlist        │   │
│  └────────────────────────────┬────────────────────────────────────┘   │
│                               │ HTTP REST API                           │
│  ┌────────────────────────────▼────────────────────────────────────┐   │
│  │                      FASTAPI BACKEND                             │   │
│  │  /scan  /opportunities  /stock  /history  /watchlist  /alerts   │   │
│  └────────────────────────────┬────────────────────────────────────┘   │
│                               │                                         │
│        ┌──────────────────────┼──────────────────────┐                 │
│        │                      │                      │                 │
│        ▼                      ▼                      ▼                 │
│  ┌──────────┐         ┌───────────────┐      ┌─────────────┐          │
│  │  CELERY  │         │   AGENT       │      │  POSTGRESQL │          │
│  │  WORKER  │────────▶│   PIPELINE    │      │  DATABASE   │          │
│  └──────────┘         └───────┬───────┘      └─────────────┘          │
│       ▲                       │                                         │
│       │                       │                                         │
│  ┌────────┐      ┌────────────▼─────────────────────────────────┐      │
│  │ REDIS  │      │              AGENT PIPELINE                   │      │
│  │ QUEUE  │      │                                               │      │
│  │ CACHE  │      │  1. Scheduler Agent  →  triggers scan         │      │
│  └────────┘      │  2. Data Agent       →  fetch market data     │      │
│                  │  3. Signal Agent     →  detect signals        │      │
│                  │  4. Reasoning Agent  →  LLM explanation       │      │
│                  │  5. Backtest Agent   →  validate history      │      │
│                  │  6. Decision Agent   →  BUY/WATCH/AVOID       │      │
│                  │  7. Audit Agent      →  log + track outcome   │      │
│                  └──────────────────────────────────────────────┘      │
│                                       │                                 │
│        ┌──────────────────────────────┼───────────────────────┐        │
│        │                              │                       │        │
│        ▼                              ▼                       ▼        │
│  ┌──────────────┐           ┌──────────────────┐    ┌──────────────┐  │
│  │   YFINANCE   │           │   NSE PUBLIC     │    │  ANTHROPIC   │  │
│  │   PRICE DATA │           │   BULK DEALS     │    │  CLAUDE API  │  │
│  │   (Live +    │           │   FEED           │    │  (LLM)       │  │
│  │   Historical)│           │                  │    │              │  │
│  └──────────────┘           └──────────────────┘    └──────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Agent Pipeline — Detailed Flow

```
SCHEDULER AGENT
│
│  Every 15 min during market hours (9:15 AM – 3:30 PM IST)
│  Queues 100+ NSE stocks for processing
│
└──▶ [Queue: stock_scan_tasks]
         │
         │ (Celery workers pick up tasks in parallel, max 10 concurrent)
         │
         ▼
    DATA AGENT (per stock)
    │
    ├── Fetches: live price, volume
    ├── Fetches: 20-day OHLCV (from cache or yfinance)
    ├── Fetches: 2-year OHLCV (from cache or yfinance)
    ├── Fetches: NSE bulk deals last 5 days
    └── Returns: MarketData object
         │
         ▼
    SIGNAL AGENT (per stock)
    │
    ├── Breakout: current_price > max(close, 30d)?
    ├── Volume Spike: today_vol > 2.0 × avg_vol(20d)?
    ├── Bulk Deal: institutional buy in last 5 days?
    ├── Composite Score: weighted combination
    │
    ├── [IF no signals triggered]
    │       └── SKIP remaining pipeline → log "no opportunity"
    │
    └── [IF at least 1 signal triggered]
         │
         ▼
    REASONING AGENT (LLM call)
    │
    ├── Builds data-grounded prompt with signal values
    ├── Calls Claude API (claude-sonnet-4-20250514)
    ├── Validates: response contains actual data values
    └── Returns: 3–5 sentence explanation
         │
         ▼
    BACKTESTING AGENT
    │
    ├── Searches 2yr historical data for same signal pattern
    ├── Measures T+5 return for each match
    ├── Calculates: success rate, avg return, worst/best case
    └── Returns: BacktestResult (up to 5 historical cases)
         │
         ▼
    DECISION AGENT
    │
    ├── Confidence = f(signal strength, backtest quality, signal count)
    ├── Action: BUY (≥70%) / WATCH (50–69%) / AVOID (<50%)
    ├── Trade params: entry, target, stop-loss, R:R ratio
    └── Returns: Decision object
         │
         ▼
    AUDIT AGENT
    │
    ├── Persists Decision to PostgreSQL with full snapshot
    ├── Schedules T+5 outcome measurement job
    ├── Triggers alert if confidence ≥ threshold
    └── Decision available via API
```

---

## 3. Data Flow Diagram

```
EXTERNAL DATA SOURCES
        │
        │  Real-time price + volume (yfinance)
        │  Historical OHLCV 2yr (yfinance)
        │  Bulk deal data (NSE public CSV)
        │
        ▼
REDIS CACHE
   ├── Live data: TTL 5 min
   ├── 20d historical: TTL 15 min
   ├── 2yr historical: TTL 24h
   └── Bulk deals: TTL 6h
        │
        ▼ (cache miss → fetch from source)
DATA AGENT
        │
        ▼
SIGNAL COMPUTATION
   ├── Breakout detection
   ├── Volume spike detection
   └── Bulk deal detection
        │
        ▼
LLM REASONING
   └── Anthropic Claude API call
        │
        ▼
BACKTEST ENGINE
   └── Scan 2yr historical data
        │
        ▼
DECISION ENGINE
   └── Score + action + trade params
        │
        ▼
POSTGRESQL DATABASE
   ├── decisions table
   ├── scan_results table
   └── audit_logs table
        │
        ▼
FASTAPI REST API
        │
        ▼
REACT FRONTEND
```

---

## 4. Frontend Page Architecture

```
App.tsx (React Router)
│
├── / → Dashboard.tsx
│         ├── MarketPulseSummary
│         ├── TopOpportunitiesPreview
│         └── WatchlistQuickView
│
├── /scanner → Scanner.tsx
│         ├── ScanControls (ScanButton + Stats)
│         ├── FilterBar
│         └── OpportunityList
│               └── OpportunityCard × N
│
├── /stock/:symbol → StockDetail.tsx
│         └── StockTabs
│               ├── OverviewTab
│               │     ├── PriceHeader
│               │     ├── ReasoningBox (LLM text)
│               │     └── DecisionCard (BUY/WATCH/AVOID)
│               ├── SignalsTab
│               │     ├── BreakoutSignalCard
│               │     ├── VolumeSpikeCard
│               │     └── BulkDealCard
│               ├── BacktestTab
│               │     ├── BacktestStats
│               │     └── HistoricalCasesTable
│               ├── TradePlanTab
│               │     ├── EntryTargetStopLoss
│               │     └── ConfidenceBreakdown
│               └── ChartTab
│                     ├── PriceChart
│                     ├── VolumeChart
│                     └── SignalMarkers
│
├── /history → History.tsx
│         ├── TrackRecordStats (win rate, total decisions)
│         ├── FilterBar (date, outcome, symbol)
│         └── DecisionTable → DecisionDetail (modal)
│
├── /watchlist → Watchlist.tsx
│         └── WatchlistCard × N
│
└── /alerts → Alerts.tsx
          └── AlertItem × N
```

---

## 5. Database Entity Relationships

```
stocks (master list)
   │
   │ 1:N
   ▼
scan_results ←──── scan_runs
   │                    (1 scan run → many scan results)
   │ 1:1
   ▼
decisions
   │
   │ 1:1
   ▼
decision_outcomes (T+5 measurements)

watchlist_items (user's tracked stocks)
alerts (triggered notifications)
market_data_cache (Redis alternative store)
bulk_deals (NSE institutional data)
system_settings (config key-value)
audit_logs (system event log)
```

---

## 6. Infrastructure Overview

```
┌──────────────────────────────────────────┐
│           PRODUCTION (Railway)           │
│                                          │
│  ┌─────────┐   ┌─────────┐              │
│  │ Backend │   │ Worker  │              │
│  │ FastAPI │   │ Celery  │              │
│  │ :8000   │   │         │              │
│  └────┬────┘   └────┬────┘              │
│       │              │                  │
│  ┌────▼──────────────▼────┐             │
│  │       Redis            │             │
│  │  Queue + Cache         │             │
│  └────────────────────────┘             │
│                                          │
│  ┌─────────────────────────┐            │
│  │      PostgreSQL         │            │
│  │   (Railway managed)     │            │
│  └─────────────────────────┘            │
│                                          │
│  ┌─────────────────────────┐            │
│  │      Frontend           │            │
│  │   React + Nginx :3000   │            │
│  └─────────────────────────┘            │
│                                          │
│  External calls:                         │
│  → yfinance (market data)               │
│  → NSE APIs (bulk deals)                │
│  → Anthropic API (LLM)                  │
└──────────────────────────────────────────┘
```

---

*Last updated: 2026-03-25 | Version: 1.0*
