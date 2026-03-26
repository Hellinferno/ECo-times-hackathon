# 01 — Project Overview & Executive Summary

## AlphaHunter AI — Autonomous Opportunity & Decision Engine

---

## 1. Executive Summary

**AlphaHunter AI** is an autonomous stock market intelligence system built for retail investors in India. It continuously monitors 100+ NSE-listed stocks, detects high-probability trading opportunities using a multi-signal detection engine, explains each opportunity in plain English backed by data, validates it against 2 years of historical patterns, and delivers a single, clear, trade-ready recommendation — complete with entry price, target, and stop-loss.

The system is not a chatbot, not a news summarizer, and not a stock screener. It is a **decision engine**: a structured pipeline of autonomous agents that converts raw market data into auditable, explainable, actionable intelligence.

---

## 2. The Problem

India has over **9.5 crore retail equity investors** — and the vast majority of them lose money or underperform the market. The core reason is not lack of data. The core reason is lack of **intelligence applied to data**.

Retail investors today:
- React to WhatsApp tips and social media rumors
- Cannot read financial filings or interpret technical charts
- Miss time-sensitive opportunities because they aren't watching the market
- Don't know *when* to act, *why* to act, or *how much risk* they're taking

> **The gap is not information. The gap is a system that converts information into decisions.**

Existing tools — broker apps, screeners, news aggregators — show data. None of them explain the reasoning, prove it with history, and tell the user exactly what to do.

---

## 3. The Solution

AlphaHunter AI closes this gap through a **5-step autonomous pipeline:**

```
Detect → Explain → Validate → Decide → Audit
```

### Step 1 — Detect
The system continuously scans 100+ NSE stocks every 15 minutes during market hours, looking for three types of signals:

- **Breakout Signal** — Price crosses above the 30-day resistance level
- **Volume Spike Signal** — Today's volume exceeds 2× the 20-day average (unusual buying pressure)
- **Bulk Deal Signal** — Institutional investor (mutual fund, FII) executed a bulk purchase in the last 5 days

### Step 2 — Explain
For every triggered signal, a large language model (Anthropic Claude) generates a 3–5 sentence explanation that references actual data values. Not "looks bullish." Instead: *"Infosys crossed its ₹1,500 resistance (30-day level) with 2.3× volume. Axis Mutual Fund bought 500,000 shares at ₹1,495 on March 22."*

### Step 3 — Validate
The system searches the last 2 years of price history to find the last 5 times the same pattern occurred and measures what happened next. It reports: **success rate**, **average return**, **worst case**, and **best case**. This turns a signal into a proof statement.

### Step 4 — Decide
Signal strength, backtest quality, and signal count are combined into a **confidence score (0–100)**. The system outputs:
- **Action:** BUY / WATCH / AVOID
- **Entry Price, Target Price, Stop-Loss**
- **Risk:Reward Ratio**

### Step 5 — Audit
Every decision is logged with a full data snapshot. Outcomes are measured automatically at T+5 trading days. The **track record is visible** — wins and losses both — so users can evaluate the system's reliability over time.

---

## 4. What Makes This Different

| Feature | Generic Screener | AI Finance Tools | **AlphaHunter AI** |
|---------|-----------------|-----------------|---------------------|
| Signal Detection | ✅ | ✅ | ✅ |
| Data-Linked Explanation | ❌ | Partial | ✅ Every sentence |
| Historical Validation | ❌ | ❌ | ✅ Backtesting |
| Specific Trade Parameters | ❌ | ❌ | ✅ Entry/Target/SL |
| Decision Audit Trail | ❌ | ❌ | ✅ Full replay |
| Outcome Tracking | ❌ | ❌ | ✅ T+5 measured |
| Institutional Signal | Partial | ❌ | ✅ Bulk deals |

**The killer differentiator:** We prove our suggestions work using history. Every BUY recommendation comes with a backtest that shows what happened the last 5 times this exact pattern appeared.

---

## 5. System Architecture (High Level)

AlphaHunter AI is built as a **multi-agent pipeline** where each agent has a single, well-defined responsibility:

```
Scheduler Agent
      ↓
Data Agent          ← yfinance + NSE bulk deals
      ↓
Signal Agent        ← Rule-based: breakout, volume, bulk deal
      ↓
Reasoning Agent     ← LLM: data-grounded plain-English explanation
      ↓
Backtesting Agent   ← 2-year historical validation
      ↓
Decision Agent      ← Confidence score + trade parameters
      ↓
Audit Agent         ← Persist, track, measure outcomes
      ↓
REST API + React Frontend
```

**Technology Stack:**

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI |
| Agent Orchestration | Celery + Redis |
| Signals | Rule-based (NumPy, pandas) |
| LLM | Anthropic Claude API |
| Data | yfinance, NSE public feeds |
| Database | PostgreSQL |
| Frontend | React + TypeScript + Tailwind CSS |
| Infrastructure | Docker Compose / Railway |

---

## 6. Key Metrics & Targets

| Metric | Target |
|--------|--------|
| Stocks scanned per cycle | 100+ |
| Scan completion time | < 60 seconds |
| BUY recommendation win rate | > 65% |
| Average return on BUY (T+5) | > 3% |
| LLM reasoning data-link rate | 100% |
| Decision audit coverage | 100% |

---

## 7. Product Scope — MVP

### In Scope
- Market scanner: 100+ NSE stocks, 3 signal types
- Stock detail: 5-tab breakdown (Overview, Signals, Backtest, Trade Plan, Chart)
- Decision engine: BUY/WATCH/AVOID + confidence + entry/target/stop-loss
- Audit trail: full decision log with outcome tracking
- Watchlist: user-tracked stocks
- Alerts: in-app signal notifications
- History dashboard: track record with win rate

### Out of Scope (MVP)
- User authentication (single-user for demo)
- Email / SMS alerts
- Options / F&O analysis
- Automated trade execution
- News sentiment analysis
- Mobile app

---

## 8. Document Index

This project is documented across the following files:

| # | Document | Description |
|---|----------|-------------|
| 01 | **Project Overview** *(this file)* | Executive summary, problem, solution, architecture |
| 02 | User Stories & Acceptance Criteria | 23 user stories across 8 epics with measurable criteria |
| 03 | Information Architecture | Site map, navigation, page inventory, content models |
| 04 | System Architecture | Agent definitions, tech stack, data flow, performance targets |
| 05 | Database Schema | PostgreSQL tables, indexes, views, migration strategy |
| 06 | API Contracts | REST API spec — all endpoints, request/response shapes |
| 07 | Monorepo Structure | Full folder tree, Docker Compose, Makefile |
| 08 | Computation Engine Spec | Signal formulas, scoring math, LLM prompts, backtest algorithm |
| 09 | Engineering Scope Definition | IN/OUT of scope, constraints, quality standards, risk register |
| 10 | Development Phases | Hour-by-hour hackathon build plan + post-hackathon roadmap |
| 11 | Environment & DevOps | `.env` config, deployment, CI/CD, monitoring |
| 12 | Testing Strategy | 30+ test cases for every agent, E2E demo flow test |
| — | Architecture Diagram | ASCII diagrams: system, agent pipeline, data flow, infra |
| — | Project Design | Product design philosophy, UX journey, competitive analysis |
| — | Market Readiness Plan | GTM, pricing, SEBI compliance, revenue projections |

---

## 9. Demo Flow (Hackathon Presentation)

The intended 3–5 minute demo script:

1. **Open Dashboard** → *"Here's today's market pulse — 7 opportunities detected."*
2. **Click "Scan Market"** → *"System scanning 100+ NSE stocks in real time."*
3. **Results appear** → *"Ranked by confidence. Let's look at the top pick."*
4. **Click INFY** → *Overview Tab: "BUY, 78% confidence. Here's why..."*
5. **Signals Tab** → *"Breakout at ₹1,500. Volume 2.3×. Axis MF bulk buy."*
6. **Backtest Tab** → *"4 out of 5 similar patterns were profitable. Avg +5.2%."*
7. **Trade Plan Tab** → *"Entry ₹1,502. Target ₹1,580. Stop-loss ₹1,455. R:R = 2.3."*
8. **History Page** → *"Here's our track record — 71% win rate across 28 past decisions."*
9. **Click a past decision** → *"Full replay. This is what the system knew, and this is what happened."*

---

## 10. Impact Statement

> If AlphaHunter AI helps a retail investor with ₹5 lakh improve their annual return by just 2%, that's ₹10,000 per year per user.
>
> At 1 lakh users, that's **₹100 crore of measurable financial impact** — delivered through data, not tips.

---

## 11. Team & Contact

| Field | Details |
|-------|---------|
| Project Name | AlphaHunter AI |
| Category | FinTech / AI Decision Engine |
| Target Market | Retail equity investors, NSE India |
| Stage | Hackathon MVP |
| Version | 1.0 |
| Last Updated | 2026-03-25 |

---

*This document is the entry point for all AlphaHunter AI project documentation. Start here, then follow the document index above.*
