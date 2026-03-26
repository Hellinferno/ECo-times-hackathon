# 04 — System Architecture

## AlphaHunter AI — Opportunity & Decision Engine

---

## 1. Overview

This document defines the full system architecture of AlphaHunter AI — a multi-agent autonomous decision engine for stock market opportunity detection. The system is designed as a pipeline of modular agents, each with a single responsibility, feeding outputs into the next stage.

---

## 2. Architecture Principles

| Principle | Application |
|-----------|-------------|
| **Single Responsibility** | Each agent does one job; no agent handles data + reasoning + UI |
| **Auditability** | Every decision logged with full data snapshot |
| **Fail-Safe** | Agent failures degrade gracefully; system reports errors without crashing |
| **Stateless Agents** | Agents receive full context per call; no hidden state |
| **Data-Driven Reasoning** | LLM reasoning is always grounded in structured signal data |

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                    ALPHAHUNTER AI                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│   ┌──────────┐   ┌──────────┐   ┌───────────────┐  │
│   │ Scheduler│──▶│   Data   │──▶│    Signal     │  │
│   │  Agent   │   │  Agent   │   │    Agent      │  │
│   └──────────┘   └──────────┘   └───────┬───────┘  │
│                                         │           │
│   ┌──────────────────────────────────── ▼ ───────┐  │
│   │              Reasoning Agent (LLM)           │  │
│   └──────────────────────────────────┬───────────┘  │
│                                      │              │
│   ┌──────────┐   ┌──────────────────▼────────────┐  │
│   │Backtest  │◀──│         Decision Agent        │  │
│   │  Agent   │──▶│                               │  │
│   └──────────┘   └───────────────────────────────┘  │
│                                      │              │
│   ┌──────────────────────────────────▼────────────┐  │
│   │               Audit Agent                    │  │
│   └──────────────────────────────────────────────┘  │
│                                      │              │
│   ┌──────────────────────────────────▼────────────┐  │
│   │              API / UI Layer                   │  │
│   └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 4. Agent Definitions

### 4.1 Scheduler Agent

**Role:** Orchestrates periodic scan cycles

**Responsibilities:**
- Triggers scan pipeline every 15 minutes during market hours (9:15 AM – 3:30 PM IST)
- Manages scan queue for 100+ stocks
- Handles backpressure (rate limiting of external API calls)
- Emits scan lifecycle events: `scan.started`, `scan.completed`, `scan.failed`

**Technology:** Python `APScheduler` or `Celery Beat`

**Inputs:** System clock, market hours config
**Outputs:** Scan trigger events with stock list

---

### 4.2 Data Agent

**Role:** Fetches and normalizes all market data

**Responsibilities:**
- Fetches real-time price and volume data (NSE via yfinance or NSE Python library)
- Fetches historical OHLCV data (2 years lookback)
- Fetches bulk deal / institutional activity data (NSE bulk deals CSV endpoint)
- Normalizes data into standard internal schema
- Caches data to reduce redundant API calls (TTL: 5 minutes for live, 24h for historical)

**Technology:** Python, `yfinance`, `pandas`, Redis cache

**Inputs:** Stock symbol list
**Outputs:** Normalized `MarketData` objects per stock

**Data fetched per stock:**
```python
{
  "symbol": "INFY",
  "current_price": 1502.45,
  "volume_today": 4600000,
  "ohlcv_20d": [...],      # last 20 days OHLCV
  "ohlcv_2yr": [...],      # 2 years OHLCV for backtest
  "bulk_deals_5d": [...]   # bulk deals in last 5 days
}
```

---

### 4.3 Signal Agent

**Role:** Detects technical and fundamental signals using rule-based logic

**Responsibilities:**
- Evaluates breakout signal: `current_price > max(close, 30d)`
- Evaluates volume spike: `today_volume > 2.0 * avg_volume(20d)`
- Evaluates bulk deal: presence of institutional buy in last 5 days
- Computes signal strength scores (0–1 per signal)
- Composes composite signal object

**Technology:** Python, NumPy, pandas

**Inputs:** `MarketData` object
**Outputs:** `SignalReport` object

```python
{
  "symbol": "INFY",
  "signals": {
    "breakout": {
      "triggered": True,
      "resistance_level": 1500,
      "current_price": 1502.45,
      "pct_above": 0.16,
      "strength": 0.72
    },
    "volume_spike": {
      "triggered": True,
      "ratio": 2.3,
      "strength": 0.85
    },
    "bulk_deal": {
      "triggered": True,
      "buyer": "Axis Mutual Fund",
      "quantity": 500000,
      "strength": 0.90
    }
  },
  "composite_score": 0.82
}
```

---

### 4.4 Reasoning Agent (LLM)

**Role:** Converts structured signal data into human-readable, data-grounded explanation

**Responsibilities:**
- Receives `SignalReport` as structured input
- Constructs a tightly constrained LLM prompt
- Returns 3–5 sentence explanation referencing exact data values
- Validates that output is data-linked (post-processing check)

**Technology:** Python, Anthropic Claude API (`claude-sonnet-4-20250514`)

**Inputs:** `SignalReport` object
**Outputs:** `ReasoningText` string

**Prompt template:**
```
You are a professional stock market analyst. Given the following signal data for a stock, write a 3-5 sentence explanation of why this is an opportunity. EVERY sentence must reference a specific data value. Do not use generic phrases.

Signal Data:
{signal_json}

Write the explanation now:
```

**Example output:**
> "Infosys crossed its 30-day resistance of ₹1,500 at ₹1,502, a level that has held for 4 weeks. Volume today reached 4.6M shares — 2.3x the 20-day average of 2.0M — indicating strong institutional demand. Axis Mutual Fund executed a bulk purchase of 500,000 shares at ₹1,495 on March 22, confirming smart-money accumulation. Historical breakout patterns on Infosys show a 4/5 success rate with average 5.2% gain within 5 days."

---

### 4.5 Backtesting Agent

**Role:** Validates signal quality by measuring historical performance of similar patterns

**Responsibilities:**
- Searches 2-year historical data for similar signal occurrences
- Matching criteria: same signal type(s) triggered within same conditions
- Measures price performance at T+3 and T+5 days after each signal
- Calculates: success rate, average return, worst case, best case
- Returns top 5 matching historical cases with details

**Technology:** Python, pandas, NumPy

**Algorithm:**
```python
def find_similar_signals(symbol, signal_type, lookback_years=2):
    historical_data = get_2yr_ohlcv(symbol)
    matches = []
    for i in range(30, len(historical_data) - 5):
        if signal_type == "breakout":
            if historical_data[i].close > max(historical_data[i-30:i].close):
                return_5d = (historical_data[i+5].close - historical_data[i].close) / historical_data[i].close
                matches.append({date: ..., return: return_5d})
    return matches[-5:]  # last 5 occurrences
```

**Inputs:** `SignalReport` + `MarketData`
**Outputs:** `BacktestResult` object

```python
{
  "matches": 5,
  "success_rate": 80.0,
  "avg_return_pct": 5.2,
  "worst_case_pct": -3.1,
  "best_case_pct": 9.8,
  "cases": [
    {"date": "2025-11-10", "return_pct": 6.1, "profitable": True},
    ...
  ]
}
```

---

### 4.6 Decision Agent

**Role:** Synthesizes all signals, reasoning, and backtest data into a final trade recommendation

**Responsibilities:**
- Computes weighted confidence score from: signal strength (40%), backtest success rate (40%), composite signal count (20%)
- Maps confidence to action: BUY (≥70%), WATCH (50–69%), AVOID (<50%)
- Calculates trade parameters: entry, target, stop-loss, R:R ratio
- Produces final `Decision` object

**Confidence Scoring Formula:**
```python
confidence = (
    signal_composite_score * 0.40 +
    (backtest_success_rate / 100) * 0.40 +
    (min(signal_count, 3) / 3) * 0.20
) * 100
```

**Trade Parameter Calculation:**
```python
entry = current_price
target = entry * (1 + avg_backtest_return / 100)
stop_loss = resistance_level * 0.97  # 3% below resistance
rr_ratio = (target - entry) / (entry - stop_loss)
```

**Inputs:** `SignalReport` + `ReasoningText` + `BacktestResult`
**Outputs:** `Decision` object

---

### 4.7 Audit Agent

**Role:** Persists decision records, measures outcomes, and maintains replay capability

**Responsibilities:**
- Stores full `Decision` object with data snapshot at decision time
- Schedules T+5 outcome measurement job per decision
- Updates decision record with actual outcome
- Provides decision log query interface
- Exports decision history to CSV

**Technology:** Python, SQLite / PostgreSQL

**Inputs:** `Decision` object (at creation), actual price (at T+5)
**Outputs:** Persisted `DecisionRecord` with outcome

---

## 5. Technology Stack

### Backend
| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Web Framework | FastAPI |
| Task Queue | Celery + Redis |
| Scheduler | APScheduler |
| Data Fetching | yfinance, requests |
| Data Processing | pandas, NumPy |
| LLM | Anthropic Claude API |
| Database | PostgreSQL (prod) / SQLite (dev) |
| Cache | Redis |
| ORM | SQLAlchemy |

### Frontend
| Layer | Technology |
|-------|-----------|
| Framework | React + TypeScript |
| State Management | Zustand |
| Charts | Recharts / TradingView Lightweight Charts |
| Styling | Tailwind CSS |
| API Client | Axios + React Query |

### Infrastructure
| Layer | Technology |
|-------|-----------|
| Containerization | Docker + Docker Compose |
| Hosting | AWS EC2 / Railway / Render |
| Environment Config | `.env` files + python-dotenv |
| Logging | Python `logging` + structured JSON logs |

---

## 6. Data Flow Sequence

```
Scheduler
  │
  ├─ Triggers scan for [INFY, TCS, RELIANCE, ...]
  │
  ▼
Data Agent (per stock, parallel)
  │
  ├─ Returns: price, volume, history, bulk deals
  │
  ▼
Signal Agent (per stock)
  │
  ├─ Returns: triggered signals + composite score
  │
  ├─ [IF no signals triggered → skip remaining pipeline]
  │
  ▼
Reasoning Agent (LLM call)
  │
  ├─ Returns: explanation text
  │
  ▼
Backtesting Agent
  │
  ├─ Returns: historical success rate + cases
  │
  ▼
Decision Agent
  │
  ├─ Returns: action + confidence + trade params
  │
  ▼
Audit Agent
  │
  ├─ Persists decision to DB
  │
  ▼
API Layer
  │
  └─ Serves results to frontend
```

---

## 7. API Architecture

- **REST API** built with FastAPI
- Endpoints:
  - `POST /api/scan` — trigger a full market scan
  - `GET /api/opportunities` — retrieve latest scan results
  - `GET /api/stock/{symbol}` — full detail for a stock
  - `GET /api/history` — past decision log
  - `GET /api/history/{id}` — single decision detail
  - `GET /api/watchlist` — user's watchlist
  - `POST /api/watchlist/{symbol}` — add to watchlist
  - `DELETE /api/watchlist/{symbol}` — remove from watchlist

---

## 8. Failure Handling

| Failure | Behavior |
|---------|----------|
| yfinance API timeout | Retry 3x with backoff; skip stock if all retries fail |
| LLM API failure | Return signal data without reasoning; flag as "reasoning unavailable" |
| Backtest data insufficient | Return partial result with note "Insufficient history" |
| Database write failure | Log error; still return result to frontend; retry write async |
| Bulk deal feed unavailable | Skip fundamental signal; continue with technical signals only |

---

## 9. Performance Targets

| Metric | Target |
|--------|--------|
| Full scan (100 stocks) | < 60 seconds |
| Single stock detail | < 3 seconds |
| LLM reasoning call | < 5 seconds |
| Dashboard load | < 1.5 seconds |
| API response (cached) | < 200ms |

---

*Last updated: 2026-03-25 | Version: 1.0*
