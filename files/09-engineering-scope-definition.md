# 09 â€” Engineering Scope Definition

## AlphaHunter AI â€” Opportunity & Decision Engine

---

## 1. Purpose

This document defines the boundaries of what will and will not be built for AlphaHunter AI. It prevents scope creep, aligns all contributors on priorities, and provides a clear "done" definition for the hackathon MVP and future phases.

---

## 2. Scope Philosophy

> **Build less, but make what you build work perfectly.**

The goal is a system where every feature that exists is polished, functional, and impressive â€” not a system with 30 half-finished features.

---

## 3. IN Scope â€” MVP (Hackathon Build)

These are non-negotiable for a competitive demo.

### 3.1 Core Pipeline

| Feature | Description | Why It's In |
|---------|-------------|-------------|
| Market Scanner | Scan 100+ NSE stocks for signals | Core product |
| Breakout Detection | Price > 30-day resistance | Primary signal |
| Volume Spike Detection | Volume > 2x 20-day average | Primary signal |
| Bulk Deal Detection | NSE institutional buy in last 5 days | Differentiating signal |
| LLM Reasoning | Data-grounded explanation per stock | Judges love this |
| Backtesting Engine | Historical success rate for same pattern | Killer differentiator |
| Decision Engine | BUY / WATCH / AVOID + confidence score | Core output |
| Trade Parameters | Entry, Target, Stop-Loss, R:R | Actionable output |
| Audit Trail | Log every decision with full snapshot | Trust builder |
| Outcome Tracking | Measure T+5 returns for past decisions | Credibility proof |

### 3.2 Data Layer

| Feature | Description |
|---------|-------------|
| yfinance Integration | Real-time + historical price/volume |
| NSE Bulk Deals Feed | Institutional activity data |
| Redis Caching | Reduce redundant API calls |
| 2-year historical store | For backtesting |

### 3.3 Frontend

| Feature | Description |
|---------|-------------|
| Dashboard | Market pulse summary |
| Scanner Page | Scan + ranked opportunity list |
| Stock Detail Page | Full 5-tab analysis view |
| History / Audit Page | Past decisions + win rate |
| Watchlist | Save and monitor specific stocks |
| Alert Notifications | In-app signal alerts |

### 3.4 Infrastructure

| Feature | Description |
|---------|-------------|
| Docker Compose | Local dev + demo environment |
| PostgreSQL | Decision and scan persistence |
| FastAPI Backend | REST API |
| React Frontend | Dashboard UI |
| Celery Worker | Background scan jobs |

---

## 4. OUT of Scope â€” MVP

These will NOT be built for the hackathon. Any time spent on these is wasted.

| Feature | Why Excluded |
|---------|-------------|
| User authentication / login | Single-user system for MVP |
| Email / SMS alerts | In-app alerts sufficient for demo |
| Options / F&O analysis | Scope too large; equities only |
| Sentiment analysis (news NLP) | Adds complexity without proven value for MVP |
| Portfolio tracking (actual positions) | Not a portfolio manager |
| Price prediction (ML models) | Rule-based signals are more explainable |
| Payment / subscription | Out of scope for hackathon |
| Mobile app | Web-only for MVP |
| Multi-user / team features | Single user |
| International markets (US, EU) | NSE India only |
| Automated trade execution | Recommendation only, not execution |
| Real-time WebSocket streaming | Polling is sufficient |
| Advanced charting (TradingView Pro) | Basic charts sufficient |
| Screener with 50+ filters | 3 signals is enough |
| AI-generated stock reports (PDF) | Out of scope |
| Backtesting with custom date ranges | Standard 2-year lookback sufficient |

---

## 5. Deferred to Phase 2

Features that are good ideas but not for MVP.

| Feature | Phase |
|---------|-------|
| Email / SMS alerts | Phase 2 |
| Sentiment analysis (news NLP) | Phase 2 |
| Additional signal types (RSI, MACD) | Phase 2 |
| Multi-user authentication | Phase 2 |
| Mobile-responsive redesign | Phase 2 |
| Advanced backtesting UI | Phase 2 |
| Performance analytics dashboard | Phase 2 |
| BSE data integration | Phase 2 |
| Webhooks for external integrations | Phase 3 |
| White-label / B2B version | Phase 3 |

---

## 6. Technical Constraints

These constraints define the engineering boundaries.

| Constraint | Specification |
|------------|--------------|
| Data provider | yfinance (free tier) + NSE public endpoints only |
| LLM provider | Gemini API only |
| Stock universe | NSE-listed equities, top 100â€“200 by volume |
| Historical data | Max 2 years (yfinance free limit) |
| Backtest window | Last 5 matching occurrences |
| Scan interval | Every 15 minutes during market hours |
| Concurrency | Max 10 parallel stock scans at a time |
| API rate limiting | Respect yfinance rate limits (< 2000 calls/day) |
| Language | Python (backend), TypeScript/React (frontend) |
| Deployment | Single-server Docker setup (no Kubernetes) |

---

## 7. Quality Standards

### 7.1 What We Will NOT Compromise On

| Standard | Requirement |
|----------|------------|
| Reasoning quality | Every LLM explanation must reference actual data values. No generic phrases. |
| Backtest integrity | Historical matches must be real â€” no synthetic or fake data. |
| Decision auditability | Every decision stored with full snapshot. No black-box outputs. |
| Signal accuracy | Each signal must meet exact threshold â€” no approximations. |
| API reliability | All API errors return structured error responses. No unhandled exceptions in prod. |

### 7.2 Acceptable Shortcuts (MVP Only)

| Shortcut | Justification |
|----------|--------------|
| No authentication | Single-user demo; add in Phase 2 |
| SQLite for dev | PostgreSQL for prod; SQLite acceptable for local testing only |
| Basic charting | Recharts is sufficient; TradingView integration deferred |
| Manual bulk deal data refresh | Auto-refresh via scheduler in Phase 2 |
| No unit test coverage for UI | Backend logic tests required; frontend UI tests deferred |

---

## 8. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| yfinance API downtime during demo | Medium | High | Cache last successful data; show "data as of X" |
| LLM API latency > 5 seconds | Medium | Medium | Show signal data immediately; load reasoning async |
| Insufficient historical data for backtest | Low | Medium | Gracefully show "Insufficient history" without crashing |
| Bulk deal data unavailable | Low | Low | Skip signal; continue with technical signals only |
| False positive signals on illiquid stocks | Medium | Medium | Filter stocks by minimum 30-day avg volume > 500K |
| Overfitting to recent market conditions | Medium | Medium | Document limitation; show backtest period clearly |

---

## 9. Success Criteria

The MVP is complete when:

- [ ] System scans 100 NSE stocks in under 60 seconds
- [ ] All 3 signal types working: Breakout, Volume Spike, Bulk Deal
- [ ] LLM reasoning generated for every BUY opportunity
- [ ] Backtesting returns success rate + avg return for every BUY
- [ ] Trade parameters (entry/target/stop-loss) shown for every BUY
- [ ] Decision log persisted with full snapshot
- [ ] T+5 outcome measurement running automatically
- [ ] Past decisions dashboard showing win rate
- [ ] Frontend demo: can click "Scan Market" and get results end-to-end
- [ ] Zero unhandled crashes during demo flow

---

## 10. Scope Change Process

Any addition to scope requires:
1. Written justification for why it's essential for MVP
2. Estimate of time to build
3. Trade-off: what existing scope item gets removed or reduced
4. Team agreement before starting

**Default answer to scope change requests: No.**

---

*Last updated: 2026-03-25 | Version: 1.0*
