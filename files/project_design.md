# Project Design

## AlphaHunter AI â€” Opportunity & Decision Engine

---

## 1. Product Vision

> AlphaHunter AI is an autonomous stock market intelligence engine that detects opportunities, explains the reasoning behind them, validates them with historical data, and delivers a clear, actionable trade recommendation â€” so that retail investors can make confident decisions without financial expertise.

---

## 2. Problem Statement

Retail investors in India collectively manage trillions of rupees in equity investments, yet the vast majority of them:

- React to tips and rumors rather than data
- Lack the tools to read financial filings or interpret charts
- Miss time-sensitive opportunities because they're not watching the market
- Don't know *when* to act, even when they've identified a stock

**The gap is not data. The gap is intelligence.** Data exists everywhere. What retail investors need is a system that converts raw data into clear decisions with verifiable logic.

---

## 3. Solution Design

AlphaHunter AI addresses this gap through a five-step pipeline:

### Step 1 â€” Detect
Continuously monitors 100+ NSE stocks for three types of signals:
- **Breakout**: Price crosses 30-day resistance level
- **Volume Spike**: Volume exceeds 2x the 20-day average
- **Bulk Deal**: Institutional investor buys in the last 5 days

### Step 2 â€” Explain
Uses a large language model (Gemini) to convert raw signal data into a plain-English explanation that references exact data values â€” not generic analysis.

### Step 3 â€” Validate
Runs a backtest on the last 2 years of price data to find the last 5 times the same pattern occurred and measure what happened next. Produces: success rate, average return, worst case.

### Step 4 â€” Decide
Synthesizes signal strength, backtest quality, and signal count into a confidence score. Maps to: **BUY** (â‰¥70%), **WATCH** (50â€“69%), or **AVOID** (<50%). Generates specific entry price, target, and stop-loss.

### Step 5 â€” Audit
Logs every decision with a full data snapshot. Measures actual outcomes at T+5 days. Maintains a visible track record so users can evaluate the system's reliability over time.

---

## 4. Design Principles

### 4.1 Every Output Must Be Explainable
No black-box recommendations. Every BUY/WATCH/AVOID maps to specific signals, reasoning, and historical evidence. Users should be able to verify any claim.

### 4.2 Data-Grounded Reasoning
The LLM reasoning is not allowed to produce generic phrases. Every sentence must reference an actual data value from the signal computation. This is enforced programmatically.

### 4.3 Proof Over Prediction
The backtesting engine doesn't predict the future â€” it shows what happened in similar situations historically. This honest framing builds trust and sets the right expectations.

### 4.4 Actionable, Not Informational
The output is not "here are some interesting signals." It is: "Here is what to do. Here is the entry price. Here is where to exit. Here is your stop-loss." This makes the system useful, not just interesting.

### 4.5 Trust Through Transparency
The audit trail shows wins AND losses. Users can see where the system was wrong. This honesty, counter-intuitively, builds more trust than a system that only shows wins.

---

## 5. User Experience Design

### Primary User Journey

```
User opens app
   â†“
Dashboard shows today's market pulse
   â†“
User clicks "Scan Market"
   â†“
System scans 100+ stocks in under 60 seconds
   â†“
Ranked list of 5â€“10 opportunities appears
   â†“
User clicks top opportunity (e.g., INFY)
   â†“
Overview Tab: Price, reasoning, BUY badge, 78% confidence
   â†“
Signals Tab: Breakout at â‚¹1,500, Volume 2.3x, Bulk deal by Axis MF
   â†“
Backtest Tab: 4/5 similar patterns profitable, avg +5.2%
   â†“
Trade Plan Tab: Entry â‚¹1,502 | Target â‚¹1,580 | SL â‚¹1,455 | R:R 2.3
   â†“
User executes trade in their broker
   â†“
5 days later: History page shows +4.8% outcome, win logged
```

### Design Values
- **Confidence over clutter**: The BUY badge and confidence score must be the most visually prominent elements
- **Depth on demand**: Full details are one tab away, not on the main screen
- **Track record front and center**: Win rate is visible on the History page, not buried
- **Dark, professional aesthetic**: Financial tool, not consumer app

---

## 6. Technical Design Summary

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Backend | Python + FastAPI | Best ecosystem for data science + finance |
| Signals | Rule-based (no ML) | Explainable, deterministic, auditable |
| LLM | Gemini 2.5 Flash | Best reasoning quality for financial explanation |
| Data | yfinance + NSE | Free, reliable, NSE-specific bulk deal data |
| Frontend | React + TypeScript | Component model fits multi-tab stock detail UX |
| Database | PostgreSQL | Reliable for decision audit trail |
| Queue | Celery + Redis | Background scans without blocking API |

---

## 7. Competitive Differentiation

| Feature | Generic Screener | Typical AI Finance Tool | AlphaHunter AI |
|---------|-----------------|------------------------|----------------|
| Signal Detection | âœ… | âœ… | âœ… |
| Plain-English Explanation | âŒ | Partial (generic) | âœ… Data-linked |
| Historical Validation | âŒ | âŒ | âœ… Backtesting |
| Trade Parameters | âŒ | âŒ | âœ… Entry/Target/SL |
| Decision Audit Trail | âŒ | âŒ | âœ… Full replay |
| Outcome Tracking | âŒ | âŒ | âœ… T+5 measurement |
| Institutional Signal | Partial | âŒ | âœ… Bulk deal detection |

**Our killer differentiator:** We prove our suggestions work using history.

---

## 8. Impact Model

### User-Level Impact
- Average retail investor portfolio: â‚¹5 lakh
- Estimated missed opportunity due to lack of intelligence: 3â€“5% per year
- AlphaHunter improvement estimate: +2% annual return
- Value per user: â‚¹10,000/year

### Scale Potential
- Target market: 10 crore+ retail equity investors in India
- 1 lakh users Ã— â‚¹10,000 value = â‚¹100 crore annual impact
- 10 lakh users = â‚¹1,000 crore annual impact

---

## 9. Success Metrics

| Metric | Target (3 months post-launch) |
|--------|-------------------------------|
| BUY recommendation win rate | > 60% |
| Average return on BUY (T+5) | > 3% |
| Scan completion time | < 60 seconds |
| LLM reasoning quality (data-linked) | 100% |
| User retention (weekly active) | > 40% |
| Watchlist stocks per user | â‰¥ 5 |

---

## 10. Limitations & Honest Disclosures

AlphaHunter AI is a decision-support tool, not a financial advisor. Users should be aware of:

- **Past performance does not guarantee future results** â€” backtesting shows historical patterns, not predictions
- **Market conditions change** â€” signals calibrated for current NSE conditions may need recalibration in bear markets
- **Data latency** â€” live data has a 5-minute delay; the system is not suitable for high-frequency or intraday trading
- **Signal false positives** â€” even 80% accuracy means 20% of BUY recommendations will not meet target
- **Not a full portfolio manager** â€” the system identifies individual opportunities; portfolio sizing and diversification remain the user's responsibility

---

*Last updated: 2026-03-25 | Version: 1.0*
