# 01 â€” Project Overview & Executive Summary

## AlphaHunter AI â€” Autonomous Opportunity & Decision Engine

---

## 1. Executive Summary

**AlphaHunter AI** is an autonomous stock market intelligence system built for retail investors in India. It continuously monitors 100+ NSE-listed stocks, detects high-probability trading opportunities using a multi-signal detection engine, explains each opportunity in plain English backed by data, validates it against 2 years of historical patterns, and delivers a single, clear, trade-ready recommendation â€” complete with entry price, target, and stop-loss.

The system is not a chatbot, not a news summarizer, and not a stock screener. It is a **decision engine**: a structured pipeline of autonomous agents that converts raw market data into auditable, explainable, actionable intelligence.

---

## 2. The Problem

India has over **9.5 crore retail equity investors** â€” and the vast majority of them lose money or underperform the market. The core reason is not lack of data. The core reason is lack of **intelligence applied to data**.

Retail investors today:
- React to WhatsApp tips and social media rumors
- Cannot read financial filings or interpret technical charts
- Miss time-sensitive opportunities because they aren't watching the market
- Don't know *when* to act, *why* to act, or *how much risk* they're taking

> **The gap is not information. The gap is a system that converts information into decisions.**

Existing tools â€” broker apps, screeners, news aggregators â€” show data. None of them explain the reasoning, prove it with history, and tell the user exactly what to do.

---

## 3. The Solution

AlphaHunter AI closes this gap through a **5-step autonomous pipeline:**

```
Detect â†’ Explain â†’ Validate â†’ Decide â†’ Audit
```

### Step 1 â€” Detect
The system continuously scans 100+ NSE stocks every 15 minutes during market hours, looking for three types of signals:

- **Breakout Signal** â€” Price crosses above the 30-day resistance level
- **Volume Spike Signal** â€” Today's volume exceeds 2Ã— the 20-day average (unusual buying pressure)
- **Bulk Deal Signal** â€” Institutional investor (mutual fund, FII) executed a bulk purchase in the last 5 days

### Step 2 â€” Explain
For every triggered signal, a large language model (Gemini) generates a 3â€“5 sentence explanation that references actual data values. Not "looks bullish." Instead: *"Infosys crossed its â‚¹1,500 resistance (30-day level) with 2.3Ã— volume. Axis Mutual Fund bought 500,000 shares at â‚¹1,495 on March 22."*

### Step 3 â€” Validate
The system searches the last 2 years of price history to find the last 5 times the same pattern occurred and measures what happened next. It reports: **success rate**, **average return**, **worst case**, and **best case**. This turns a signal into a proof statement.

### Step 4 â€” Decide
Signal strength, backtest quality, and signal count are combined into a **confidence score (0â€“100)**. The system outputs:
- **Action:** BUY / WATCH / AVOID
- **Entry Price, Target Price, Stop-Loss**
- **Risk:Reward Ratio**

### Step 5 â€” Audit
Every decision is logged with a full data snapshot. Outcomes are measured automatically at T+5 trading days. The **track record is visible** â€” wins and losses both â€” so users can evaluate the system's reliability over time.

---

## 4. What Makes This Different

| Feature | Generic Screener | AI Finance Tools | **AlphaHunter AI** |
|---------|-----------------|-----------------|---------------------|
| Signal Detection | âœ… | âœ… | âœ… |
| Data-Linked Explanation | âŒ | Partial | âœ… Every sentence |
| Historical Validation | âŒ | âŒ | âœ… Backtesting |
| Specific Trade Parameters | âŒ | âŒ | âœ… Entry/Target/SL |
| Decision Audit Trail | âŒ | âŒ | âœ… Full replay |
| Outcome Tracking | âŒ | âŒ | âœ… T+5 measured |
| Institutional Signal | Partial | âŒ | âœ… Bulk deals |

**The killer differentiator:** We prove our suggestions work using history. Every BUY recommendation comes with a backtest that shows what happened the last 5 times this exact pattern appeared.

---

## 5. System Architecture (High Level)

AlphaHunter AI is built as a **multi-agent pipeline** where each agent has a single, well-defined responsibility:

```
Scheduler Agent
      â†“
Data Agent          â† yfinance + NSE bulk deals
      â†“
Signal Agent        â† Rule-based: breakout, volume, bulk deal
      â†“
Reasoning Agent     â† LLM: data-grounded plain-English explanation
      â†“
Backtesting Agent   â† 2-year historical validation
      â†“
Decision Agent      â† Confidence score + trade parameters
      â†“
Audit Agent         â† Persist, track, measure outcomes
      â†“
REST API + React Frontend
```

**Technology Stack:**

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI |
| Agent Orchestration | Celery + Redis |
| Signals | Rule-based (NumPy, pandas) |
| LLM | Gemini API |
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

## 7. Product Scope â€” MVP

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
| 06 | API Contracts | REST API spec â€” all endpoints, request/response shapes |
| 07 | Monorepo Structure | Full folder tree, Docker Compose, Makefile |
| 08 | Computation Engine Spec | Signal formulas, scoring math, LLM prompts, backtest algorithm |
| 09 | Engineering Scope Definition | IN/OUT of scope, constraints, quality standards, risk register |
| 10 | Development Phases | Hour-by-hour hackathon build plan + post-hackathon roadmap |
| 11 | Environment & DevOps | `.env` config, deployment, CI/CD, monitoring |
| 12 | Testing Strategy | 30+ test cases for every agent, E2E demo flow test |
| â€” | Architecture Diagram | ASCII diagrams: system, agent pipeline, data flow, infra |
| â€” | Project Design | Product design philosophy, UX journey, competitive analysis |
| â€” | Market Readiness Plan | GTM, pricing, SEBI compliance, revenue projections |

---

## 9. Demo Flow (Hackathon Presentation)

The intended 3â€“5 minute demo script:

1. **Open Dashboard** â†’ *"Here's today's market pulse â€” 7 opportunities detected."*
2. **Click "Scan Market"** â†’ *"System scanning 100+ NSE stocks in real time."*
3. **Results appear** â†’ *"Ranked by confidence. Let's look at the top pick."*
4. **Click INFY** â†’ *Overview Tab: "BUY, 78% confidence. Here's why..."*
5. **Signals Tab** â†’ *"Breakout at â‚¹1,500. Volume 2.3Ã—. Axis MF bulk buy."*
6. **Backtest Tab** â†’ *"4 out of 5 similar patterns were profitable. Avg +5.2%."*
7. **Trade Plan Tab** â†’ *"Entry â‚¹1,502. Target â‚¹1,580. Stop-loss â‚¹1,455. R:R = 2.3."*
8. **History Page** â†’ *"Here's our track record â€” 71% win rate across 28 past decisions."*
9. **Click a past decision** â†’ *"Full replay. This is what the system knew, and this is what happened."*

---

## 10. Impact Statement

> If AlphaHunter AI helps a retail investor with â‚¹5 lakh improve their annual return by just 2%, that's â‚¹10,000 per year per user.
>
> At 1 lakh users, that's **â‚¹100 crore of measurable financial impact** â€” delivered through data, not tips.

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
