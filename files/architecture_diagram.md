# Architecture Diagram

## AlphaHunter AI â€” System Architecture Overview

---

## 1. Full System Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                         ALPHAHUNTER AI SYSTEM                           â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                                                         â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚  â”‚                         FRONTEND (React)                         â”‚   â”‚
â”‚  â”‚  Dashboard â”‚ Scanner â”‚ Stock Detail â”‚ History â”‚ Watchlist        â”‚   â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â”‚                               â”‚ HTTP REST API                           â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚  â”‚                      FASTAPI BACKEND                             â”‚   â”‚
â”‚  â”‚  /scan  /opportunities  /stock  /history  /watchlist  /alerts   â”‚   â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â”‚                               â”‚                                         â”‚
â”‚        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                 â”‚
â”‚        â”‚                      â”‚                      â”‚                 â”‚
â”‚        â–¼                      â–¼                      â–¼                 â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”      â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”          â”‚
â”‚  â”‚  CELERY  â”‚         â”‚   AGENT       â”‚      â”‚  POSTGRESQL â”‚          â”‚
â”‚  â”‚  WORKER  â”‚â”€â”€â”€â”€â”€â”€â”€â”€â–¶â”‚   PIPELINE    â”‚      â”‚  DATABASE   â”‚          â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜         â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜      â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜          â”‚
â”‚       â–²                       â”‚                                         â”‚
â”‚       â”‚                       â”‚                                         â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”      â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”      â”‚
â”‚  â”‚ REDIS  â”‚      â”‚              AGENT PIPELINE                   â”‚      â”‚
â”‚  â”‚ QUEUE  â”‚      â”‚                                               â”‚      â”‚
â”‚  â”‚ CACHE  â”‚      â”‚  1. Scheduler Agent  â†’  triggers scan         â”‚      â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”˜      â”‚  2. Data Agent       â†’  fetch market data     â”‚      â”‚
â”‚                  â”‚  3. Signal Agent     â†’  detect signals        â”‚      â”‚
â”‚                  â”‚  4. Reasoning Agent  â†’  LLM explanation       â”‚      â”‚
â”‚                  â”‚  5. Backtest Agent   â†’  validate history      â”‚      â”‚
â”‚                  â”‚  6. Decision Agent   â†’  BUY/WATCH/AVOID       â”‚      â”‚
â”‚                  â”‚  7. Audit Agent      â†’  log + track outcome   â”‚      â”‚
â”‚                  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜      â”‚
â”‚                                       â”‚                                 â”‚
â”‚        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”        â”‚
â”‚        â”‚                              â”‚                       â”‚        â”‚
â”‚        â–¼                              â–¼                       â–¼        â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”           â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚   YFINANCE   â”‚           â”‚   NSE PUBLIC     â”‚    â”‚  ANTHROPIC   â”‚  â”‚
â”‚  â”‚   PRICE DATA â”‚           â”‚   BULK DEALS     â”‚    â”‚  CLAUDE API  â”‚  â”‚
â”‚  â”‚   (Live +    â”‚           â”‚   FEED           â”‚    â”‚  (LLM)       â”‚  â”‚
â”‚  â”‚   Historical)â”‚           â”‚                  â”‚    â”‚              â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜           â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
â”‚                                                                         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## 2. Agent Pipeline â€” Detailed Flow

```
SCHEDULER AGENT
â”‚
â”‚  Every 15 min during market hours (9:15 AM â€“ 3:30 PM IST)
â”‚  Queues 100+ NSE stocks for processing
â”‚
â””â”€â”€â–¶ [Queue: stock_scan_tasks]
         â”‚
         â”‚ (Celery workers pick up tasks in parallel, max 10 concurrent)
         â”‚
         â–¼
    DATA AGENT (per stock)
    â”‚
    â”œâ”€â”€ Fetches: live price, volume
    â”œâ”€â”€ Fetches: 20-day OHLCV (from cache or yfinance)
    â”œâ”€â”€ Fetches: 2-year OHLCV (from cache or yfinance)
    â”œâ”€â”€ Fetches: NSE bulk deals last 5 days
    â””â”€â”€ Returns: MarketData object
         â”‚
         â–¼
    SIGNAL AGENT (per stock)
    â”‚
    â”œâ”€â”€ Breakout: current_price > max(close, 30d)?
    â”œâ”€â”€ Volume Spike: today_vol > 2.0 Ã— avg_vol(20d)?
    â”œâ”€â”€ Bulk Deal: institutional buy in last 5 days?
    â”œâ”€â”€ Composite Score: weighted combination
    â”‚
    â”œâ”€â”€ [IF no signals triggered]
    â”‚       â””â”€â”€ SKIP remaining pipeline â†’ log "no opportunity"
    â”‚
    â””â”€â”€ [IF at least 1 signal triggered]
         â”‚
         â–¼
    REASONING AGENT (LLM call)
    â”‚
    â”œâ”€â”€ Builds data-grounded prompt with signal values
    â”œâ”€â”€ Calls Gemini API (gemini-2.5-flash)
    â”œâ”€â”€ Validates: response contains actual data values
    â””â”€â”€ Returns: 3â€“5 sentence explanation
         â”‚
         â–¼
    BACKTESTING AGENT
    â”‚
    â”œâ”€â”€ Searches 2yr historical data for same signal pattern
    â”œâ”€â”€ Measures T+5 return for each match
    â”œâ”€â”€ Calculates: success rate, avg return, worst/best case
    â””â”€â”€ Returns: BacktestResult (up to 5 historical cases)
         â”‚
         â–¼
    DECISION AGENT
    â”‚
    â”œâ”€â”€ Confidence = f(signal strength, backtest quality, signal count)
    â”œâ”€â”€ Action: BUY (â‰¥70%) / WATCH (50â€“69%) / AVOID (<50%)
    â”œâ”€â”€ Trade params: entry, target, stop-loss, R:R ratio
    â””â”€â”€ Returns: Decision object
         â”‚
         â–¼
    AUDIT AGENT
    â”‚
    â”œâ”€â”€ Persists Decision to PostgreSQL with full snapshot
    â”œâ”€â”€ Schedules T+5 outcome measurement job
    â”œâ”€â”€ Triggers alert if confidence â‰¥ threshold
    â””â”€â”€ Decision available via API
```

---

## 3. Data Flow Diagram

```
EXTERNAL DATA SOURCES
        â”‚
        â”‚  Real-time price + volume (yfinance)
        â”‚  Historical OHLCV 2yr (yfinance)
        â”‚  Bulk deal data (NSE public CSV)
        â”‚
        â–¼
REDIS CACHE
   â”œâ”€â”€ Live data: TTL 5 min
   â”œâ”€â”€ 20d historical: TTL 15 min
   â”œâ”€â”€ 2yr historical: TTL 24h
   â””â”€â”€ Bulk deals: TTL 6h
        â”‚
        â–¼ (cache miss â†’ fetch from source)
DATA AGENT
        â”‚
        â–¼
SIGNAL COMPUTATION
   â”œâ”€â”€ Breakout detection
   â”œâ”€â”€ Volume spike detection
   â””â”€â”€ Bulk deal detection
        â”‚
        â–¼
LLM REASONING
   â””â”€â”€ Gemini API call
        â”‚
        â–¼
BACKTEST ENGINE
   â””â”€â”€ Scan 2yr historical data
        â”‚
        â–¼
DECISION ENGINE
   â””â”€â”€ Score + action + trade params
        â”‚
        â–¼
POSTGRESQL DATABASE
   â”œâ”€â”€ decisions table
   â”œâ”€â”€ scan_results table
   â””â”€â”€ audit_logs table
        â”‚
        â–¼
FASTAPI REST API
        â”‚
        â–¼
REACT FRONTEND
```

---

## 4. Frontend Page Architecture

```
App.tsx (React Router)
â”‚
â”œâ”€â”€ / â†’ Dashboard.tsx
â”‚         â”œâ”€â”€ MarketPulseSummary
â”‚         â”œâ”€â”€ TopOpportunitiesPreview
â”‚         â””â”€â”€ WatchlistQuickView
â”‚
â”œâ”€â”€ /scanner â†’ Scanner.tsx
â”‚         â”œâ”€â”€ ScanControls (ScanButton + Stats)
â”‚         â”œâ”€â”€ FilterBar
â”‚         â””â”€â”€ OpportunityList
â”‚               â””â”€â”€ OpportunityCard Ã— N
â”‚
â”œâ”€â”€ /stock/:symbol â†’ StockDetail.tsx
â”‚         â””â”€â”€ StockTabs
â”‚               â”œâ”€â”€ OverviewTab
â”‚               â”‚     â”œâ”€â”€ PriceHeader
â”‚               â”‚     â”œâ”€â”€ ReasoningBox (LLM text)
â”‚               â”‚     â””â”€â”€ DecisionCard (BUY/WATCH/AVOID)
â”‚               â”œâ”€â”€ SignalsTab
â”‚               â”‚     â”œâ”€â”€ BreakoutSignalCard
â”‚               â”‚     â”œâ”€â”€ VolumeSpikeCard
â”‚               â”‚     â””â”€â”€ BulkDealCard
â”‚               â”œâ”€â”€ BacktestTab
â”‚               â”‚     â”œâ”€â”€ BacktestStats
â”‚               â”‚     â””â”€â”€ HistoricalCasesTable
â”‚               â”œâ”€â”€ TradePlanTab
â”‚               â”‚     â”œâ”€â”€ EntryTargetStopLoss
â”‚               â”‚     â””â”€â”€ ConfidenceBreakdown
â”‚               â””â”€â”€ ChartTab
â”‚                     â”œâ”€â”€ PriceChart
â”‚                     â”œâ”€â”€ VolumeChart
â”‚                     â””â”€â”€ SignalMarkers
â”‚
â”œâ”€â”€ /history â†’ History.tsx
â”‚         â”œâ”€â”€ TrackRecordStats (win rate, total decisions)
â”‚         â”œâ”€â”€ FilterBar (date, outcome, symbol)
â”‚         â””â”€â”€ DecisionTable â†’ DecisionDetail (modal)
â”‚
â”œâ”€â”€ /watchlist â†’ Watchlist.tsx
â”‚         â””â”€â”€ WatchlistCard Ã— N
â”‚
â””â”€â”€ /alerts â†’ Alerts.tsx
          â””â”€â”€ AlertItem Ã— N
```

---

## 5. Database Entity Relationships

```
stocks (master list)
   â”‚
   â”‚ 1:N
   â–¼
scan_results â†â”€â”€â”€â”€ scan_runs
   â”‚                    (1 scan run â†’ many scan results)
   â”‚ 1:1
   â–¼
decisions
   â”‚
   â”‚ 1:1
   â–¼
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
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚           PRODUCTION (Railway)           â”‚
â”‚                                          â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”              â”‚
â”‚  â”‚ Backend â”‚   â”‚ Worker  â”‚              â”‚
â”‚  â”‚ FastAPI â”‚   â”‚ Celery  â”‚              â”‚
â”‚  â”‚ :8000   â”‚   â”‚         â”‚              â”‚
â”‚  â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜   â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜              â”‚
â”‚       â”‚              â”‚                  â”‚
â”‚  â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”             â”‚
â”‚  â”‚       Redis            â”‚             â”‚
â”‚  â”‚  Queue + Cache         â”‚             â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜             â”‚
â”‚                                          â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”            â”‚
â”‚  â”‚      PostgreSQL         â”‚            â”‚
â”‚  â”‚   (Railway managed)     â”‚            â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜            â”‚
â”‚                                          â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”            â”‚
â”‚  â”‚      Frontend           â”‚            â”‚
â”‚  â”‚   React + Nginx :3000   â”‚            â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜            â”‚
â”‚                                          â”‚
â”‚  External calls:                         â”‚
â”‚  â†’ yfinance (market data)               â”‚
â”‚  â†’ NSE APIs (bulk deals)                â”‚
â”‚  â†’ Gemini API (LLM)                  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

*Last updated: 2026-03-25 | Version: 1.0*
