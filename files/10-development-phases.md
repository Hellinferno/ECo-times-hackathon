# 10 — Development Phases

## AlphaHunter AI — Opportunity & Decision Engine

---

## 1. Overview

This document breaks the AlphaHunter AI build into executable phases with time estimates, sequencing logic, and milestone deliverables. It is designed as a **hackathon build plan** (compressed timeline) with a post-hackathon roadmap for production.

---

## 2. Hackathon Timeline (24–36 Hours)

### Hour-by-Hour Breakdown

```
Hour 00–02:  Environment Setup + Data Agent
Hour 02–05:  Signal Agent (Breakout + Volume Spike)
Hour 05–07:  Bulk Deal Signal + Backtesting Agent
Hour 07–09:  Decision Agent + Reasoning Agent (LLM)
Hour 09–12:  FastAPI Backend + Database
Hour 12–16:  Frontend — Scanner + Stock Detail
Hour 16–20:  Frontend — History + Audit Trail
Hour 20–24:  Integration, Polish, Demo Prep
Hour 24–28:  Buffer, Bug Fixes, Edge Cases
Hour 28–36:  Demo refinement, pitch preparation
```

---

## 3. Phase 0 — Environment Setup (Hours 0–2)

### Objectives
- Working local development environment
- Database running with schema applied
- All dependencies installed
- NSE stock list seeded

### Tasks

| Task | Owner | Duration |
|------|-------|----------|
| Create repo + folder structure from doc-07 | BE | 20 min |
| Copy `.env.example` to `.env`, fill in API keys | BE | 5 min |
| `docker-compose up` — PostgreSQL + Redis running | BE | 10 min |
| `pip install -r requirements.txt` | BE | 5 min |
| `alembic upgrade head` — schema applied | BE | 10 min |
| `python scripts/seed_stocks.py` — 100+ stocks seeded | BE | 15 min |
| Verify DB connectivity from Python | BE | 10 min |
| Set up React app (Vite + TypeScript + Tailwind) | FE | 30 min |
| Verify frontend runs on `localhost:3000` | FE | 5 min |

### Exit Criteria
- `GET /api/health` returns `200 OK`
- Database has 100+ rows in `stocks` table
- Frontend renders without errors

---

## 4. Phase 1 — Data Agent + Signal Agent (Hours 2–7)

### Objectives
- System can fetch live price and volume data for any NSE stock
- Breakout and Volume Spike signals correctly detected
- Bulk deal signal working

### Tasks

| Task | Owner | Duration |
|------|-------|----------|
| Implement `yfinance_client.py` — fetch live + historical OHLCV | BE | 45 min |
| Implement `nse_client.py` — fetch bulk deals CSV | BE | 30 min |
| Implement `cache_client.py` — Redis get/set with TTL | BE | 20 min |
| Implement `data_agent.py` — orchestrate fetches + cache | BE | 30 min |
| Implement `signal_agent.py` — breakout detection (per spec §2.1) | BE | 45 min |
| Implement `signal_agent.py` — volume spike detection (per spec §2.2) | BE | 30 min |
| Implement `signal_agent.py` — bulk deal detection (per spec §2.3) | BE | 30 min |
| Implement composite score formula (per spec §3) | BE | 20 min |
| Unit tests: `test_signal_agent.py` | BE | 30 min |

### Exit Criteria
- `signal_agent.detect_signals("INFY")` returns correctly structured `SignalReport`
- Breakout signal triggers on known historical breakout date (manual verification)
- Volume spike triggers on days with > 2x volume (manual verification)
- All unit tests passing

---

## 5. Phase 2 — Backtesting + Decision + Reasoning Agents (Hours 5–9)

### Objectives
- System validates signal quality using historical data
- Final decision generated with trade parameters
- LLM reasoning working and data-linked

### Tasks

| Task | Owner | Duration |
|------|-------|----------|
| Implement `backtesting_agent.py` — historical match finder (per spec §4.1) | BE | 60 min |
| Implement backtest statistics calculation (per spec §4.2) | BE | 20 min |
| Implement backtest quality score (per spec §4.3) | BE | 15 min |
| Implement `decision_agent.py` — confidence formula (per spec §5) | BE | 30 min |
| Implement trade parameter calculation (per spec §6) | BE | 20 min |
| Implement `reasoning_agent.py` — prompt construction + LLM call | BE | 45 min |
| Implement reasoning validation (per spec §8.2) | BE | 15 min |
| Unit tests: `test_backtesting_agent.py`, `test_decision_agent.py` | BE | 30 min |

### Exit Criteria
- For `INFY` with breakout signal: backtest returns 5 historical cases
- Confidence score computed correctly
- LLM reasoning contains actual price/volume numbers
- Trade parameters (entry/target/stop-loss) calculated

---

## 6. Phase 3 — Scan Orchestration + API (Hours 9–12)

### Objectives
- Full scan pipeline works end-to-end
- FastAPI endpoints expose data to frontend

### Tasks

| Task | Owner | Duration |
|------|-------|----------|
| Implement `scheduler_agent.py` — scan orchestration + parallelism | BE | 45 min |
| Implement Celery task `scan_task.py` | BE | 20 min |
| Implement `audit_agent.py` — decision persistence | BE | 30 min |
| Implement `outcome_task.py` — T+5 outcome measurement | BE | 20 min |
| Implement API endpoints: `/scan`, `/opportunities`, `/stock/{symbol}` | BE | 60 min |
| Implement API endpoints: `/history`, `/watchlist`, `/alerts`, `/settings` | BE | 45 min |
| Integration test: `POST /api/scan` → results via `GET /api/opportunities` | BE | 20 min |

### Exit Criteria
- Full scan of 10 stocks runs in < 30 seconds
- `GET /api/opportunities` returns ranked list
- `GET /api/stock/INFY` returns full detail including reasoning + backtest
- All API endpoints return correct response envelope structure

---

## 7. Phase 4 — Frontend Core (Hours 12–20)

### Objectives
- Scanner and Stock Detail pages fully functional
- User can run scan and explore results

### Tasks

| Task | Owner | Duration |
|------|-------|----------|
| Set up `api/client.ts` (Axios + base URL) | FE | 20 min |
| Implement all API client functions | FE | 45 min |
| Build `Scanner.tsx` — scan button, loading state, opportunity list | FE | 90 min |
| Build `OpportunityCard.tsx` — symbol, signals, action badge, confidence | FE | 45 min |
| Build `FilterBar.tsx` — action + signal type filters | FE | 30 min |
| Build `StockDetail.tsx` — page with tab navigation | FE | 30 min |
| Build `OverviewTab.tsx` — price, reasoning, decision card | FE | 60 min |
| Build `SignalsTab.tsx` — per-signal cards with data values | FE | 45 min |
| Build `BacktestTab.tsx` — case table + stats | FE | 45 min |
| Build `TradePlanTab.tsx` — entry / target / stop-loss / R:R | FE | 30 min |
| Build `ChartTab.tsx` — price chart + volume bars | FE | 60 min |
| Build `ActionBadge.tsx`, `ConfidencePill.tsx`, `LoadingSpinner.tsx` | FE | 20 min |

### Exit Criteria
- User clicks "Scan Market" → sees ranked list of opportunities
- User clicks a stock → sees all 5 tabs with real data
- LLM reasoning displayed in OverviewTab
- Backtest cases shown in BacktestTab
- Entry/Target/Stop-Loss shown in TradePlanTab

---

## 8. Phase 5 — Frontend Secondary Pages (Hours 16–20)

### Tasks

| Task | Owner | Duration |
|------|-------|----------|
| Build `Dashboard.tsx` — market pulse, top 3 opportunities | FE | 60 min |
| Build `History.tsx` — decision table with win rate stats | FE | 60 min |
| Build `DecisionDetail.tsx` — full replay modal | FE | 45 min |
| Build `Watchlist.tsx` — add/remove stocks, signal status | FE | 45 min |
| Build `Alerts.tsx` — notification inbox | FE | 30 min |
| Build `Sidebar.tsx` + navigation routing | FE | 30 min |
| Export CSV button on History page | FE | 20 min |

---

## 9. Phase 6 — Integration & Polish (Hours 20–28)

### Objectives
- End-to-end demo flow works flawlessly
- No crashes, no empty states, good error handling

### Tasks

| Task | Owner | Duration |
|------|-------|----------|
| Full end-to-end smoke test: scan → stock detail → history | Both | 30 min |
| Error states: empty opportunities, API failure, loading timeouts | FE | 30 min |
| Ensure LLM reasoning always has data values (validation) | BE | 20 min |
| Seed 7 days of historical fake decisions for History demo | BE | 20 min |
| Fine-tune confidence thresholds based on test scan results | BE | 20 min |
| UI polish: consistent colors, spacing, typography | FE | 60 min |
| Mobile responsiveness (basic) | FE | 30 min |
| Verify Docker build works on clean machine | Both | 20 min |
| Update `.env.example` with all required keys | BE | 10 min |
| Write `README.md` — setup instructions | Both | 30 min |

---

## 10. Phase 7 — Demo Preparation (Hours 28–36)

### Objectives
- Demo script rehearsed
- Pitch deck prepared
- System running in a stable, demo-ready state

### Demo Script:
1. Open Dashboard → "Here's today's market pulse"
2. Click "Scan Market" → "System scanning 100+ NSE stocks"
3. Results appear → "7 opportunities found today"
4. Click top opportunity (e.g., INFY) → walk through all 5 tabs
5. Show TradePlan → "Exact entry, target, and stop-loss"
6. Open History → "Here's our track record — 71% win rate"
7. Click a past decision → "Full replay of why we recommended it"

---

## 11. Post-Hackathon Roadmap

### Phase 8 — Production Hardening (Week 1–2)
- Add user authentication (JWT + email login)
- Move to managed PostgreSQL (Railway / Supabase)
- Add proper rate limiting + API security
- Automated test suite (70%+ coverage)
- Error monitoring (Sentry)

### Phase 9 — Feature Expansion (Month 1)
- Email / SMS alerts
- Additional signals: RSI, MACD, EMA crossover
- News sentiment integration (Google News API)
- Extended stock universe (BSE 500)
- Advanced backtesting UI with custom date ranges

### Phase 10 — Scale (Month 2–3)
- Multi-user authentication
- Freemium model (limited scans free, premium unlimited)
- Performance optimization (parallel processing, query tuning)
- API for third-party integrations

---

## 12. Build Velocity Risks

| Risk | Mitigation |
|------|------------|
| LLM API slow / expensive | Cache reasoning; only regenerate if signal changes |
| yfinance rate limited | Implement exponential backoff; cache aggressively |
| Frontend takes longer than expected | Prioritize Scanner + Stock Detail; defer History to Phase 5 |
| Backtesting calculation bugs | Test on known stocks (INFY, TCS) with verified expected output |
| Docker not working on demo machine | Have local Python + Node fallback ready |

---

*Last updated: 2026-03-25 | Version: 1.0*
