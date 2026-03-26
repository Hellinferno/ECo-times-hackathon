# Project Market Readiness Plan

## AlphaHunter AI — Opportunity & Decision Engine

---

## 1. Overview

This document defines the path from hackathon MVP to a market-ready product. It covers post-hackathon hardening, go-to-market strategy, distribution channels, monetization model, and growth milestones.

---

## 2. Market Opportunity

### 2.1 India's Retail Equity Market

| Metric | Value |
|--------|-------|
| Active NSE investors | ~9.5 crore (2025) |
| New demat accounts opened monthly | ~30 lakh |
| Avg retail portfolio size | ₹3–10 lakh |
| % of retail investors who rely on tips | ~70% |
| Gap in data-driven retail tools | **Very large** |

### 2.2 Problem Validation

The core problem AlphaHunter solves is well-validated:
- Retail investors consistently underperform institutional investors by 2–5% annually
- Primary cause: reactive, tip-driven decisions rather than systematic analysis
- Existing tools (Screeners, broker apps) provide data but not intelligence or decisions
- No mainstream free/freemium product offers backtested, explained trade recommendations

---

## 3. Readiness Stages

### Stage 1 — Hackathon MVP (Current)
- Single-user system
- Core pipeline: scan, signal, reason, backtest, decide, audit
- Demo-ready frontend
- **Goal:** Win the hackathon / prove the concept

### Stage 2 — Beta (Month 1–2)
- Multi-user with authentication
- Production-grade infrastructure
- Email alerts
- Expanded to 500 stocks
- Closed beta: 100–500 users

### Stage 3 — Public Launch (Month 3–4)
- Freemium model live
- App store listing (PWA)
- First 1,000 paid users

### Stage 4 — Growth (Month 6–12)
- Mobile app (React Native)
- Additional signal types
- Integration with broker APIs (view-only)
- 10,000+ active users

---

## 4. Go-to-Market Strategy

### 4.1 Phase 1 — Community Launch (Month 1)

**Target communities:**
- TradingQnA (NSE's official community forum — 1M+ members)
- Reddit: r/IndiaInvestments, r/IndianStreetBets
- Twitter/X: finance influencer ecosystem
- Telegram: stock tip groups (counter-position: "replace tips with data")
- YouTube: personal finance creators (demo collab)

**Launch message:**
> "Stop acting on tips. Start acting on data. AlphaHunter AI scans 100+ stocks, explains every signal, proves it with history, and tells you exactly what to do."

**Content strategy:**
- Weekly "AlphaHunter Pick" posts: share one opportunity the system found (with backtest data)
- Before/After: replace a famous bad tip with what AlphaHunter would have recommended
- Transparency posts: share the track record including losses — builds trust

---

### 4.2 Phase 2 — Influencer & Creator Distribution (Month 2–3)

**Target creators:**
- SOIC (School of Intrinsic Compounding) — 500K+ YouTube
- Pranjal Kamra (Finology) — 3M+ YouTube
- Akshat Shrivastava — 2M+ YouTube
- CA Rachana Ranade — 4M+ YouTube

**Offer:** Free premium access + revenue share for referrals

---

### 4.3 Phase 3 — SEO & Organic (Month 3+)

**Target keywords:**
- "stock breakout scanner India"
- "NSE breakout stocks today"
- "best stocks to buy today NSE"
- "institutional buying NSE stocks"
- "AI stock picker India"

**Content:** Daily/weekly "Top NSE Opportunities" pages generated from system output

---

### 4.4 Phase 4 — Partnership (Month 6+)

**Target partners:**
- Zerodha / Kite: integration with most popular broker platform
- Groww: largest retail investor base
- Smallcase: thematic basket products
- SEBI-registered Investment Advisors: tool for their advisory practice

---

## 5. Monetization Model

### 5.1 Freemium Tiers

| Feature | Free | Pro (₹499/mo) | Team (₹1,999/mo) |
|---------|------|---------------|------------------|
| Scans per day | 2 | Unlimited | Unlimited |
| Stocks scanned | Top 50 | Full 500+ | Full 500+ |
| Signal types | Breakout + Volume | All 3 signals | All 3 signals |
| Backtest results | Partial (3 cases) | Full (5 cases) | Full + custom range |
| Trade parameters | ❌ | ✅ | ✅ |
| Alerts | ❌ | 10/day | Unlimited |
| Export / CSV | ❌ | ✅ | ✅ |
| Decision history | 7 days | 90 days | 1 year |
| Priority support | ❌ | ❌ | ✅ |
| Users | 1 | 1 | 5 |

### 5.2 Revenue Projections

| Month | Free Users | Pro Users | MRR |
|-------|------------|-----------|-----|
| 3 | 500 | 50 | ₹24,950 |
| 6 | 2,000 | 200 | ₹99,800 |
| 12 | 10,000 | 800 | ₹3,99,200 |
| 18 | 30,000 | 2,000 | ₹9,98,000 |

### 5.3 Additional Revenue Streams (Phase 2+)
- B2B API for advisors and fintech apps
- White-label for broker platforms
- Premium research reports (PDF)
- Affiliate commissions from broker referrals

---

## 6. Regulatory Considerations

### SEBI Compliance
AlphaHunter AI provides:
- **Data-driven signals**: factual, based on publicly available market data ✅
- **Historical analysis**: performance based on backtesting ✅
- **Decision support**: recommendations based on systematic rules ✅

AlphaHunter AI does NOT:
- Provide personalized investment advice (SEBI RIA license required)
- Execute trades on user's behalf
- Guarantee returns

**Required disclaimers (on all pages):**
> "AlphaHunter AI is not a SEBI-registered investment advisor. All recommendations are for informational purposes only and are based on algorithmic signal detection and historical data. Past performance does not guarantee future results. Please consult a SEBI-registered advisor before making investment decisions."

**Future requirement:** If personalized recommendations grow, SEBI Research Analyst registration (RA) may be required.

---

## 7. Technical Readiness Checklist for Production

### Infrastructure
- [ ] Move from SQLite (dev) to managed PostgreSQL
- [ ] Set up Redis on managed service (Upstash / Railway)
- [ ] Configure HTTPS on all endpoints
- [ ] Set up automated database backups
- [ ] Configure proper CORS for production domain
- [ ] Implement API rate limiting

### Security
- [ ] Add JWT authentication
- [ ] Sanitize all user inputs
- [ ] Rotate all API keys from dev to prod
- [ ] Set `APP_ENV=production` (disables debug endpoints)
- [ ] Set up secret management (AWS Secrets Manager or similar)

### Reliability
- [ ] Set up error monitoring (Sentry)
- [ ] Set up uptime monitoring (Better Uptime or Pingdom)
- [ ] Configure auto-restart on crash (Docker restart policies)
- [ ] Add health check endpoint to monitoring
- [ ] Test recovery from yfinance downtime

### Performance
- [ ] Benchmark scan time with 500 stocks
- [ ] Add database indexes for all query paths
- [ ] Enable query caching for common lookups
- [ ] Test concurrent user load (target: 100 concurrent)

### Compliance
- [ ] Add risk disclaimer to every page
- [ ] Add disclaimer to all BUY recommendations
- [ ] Privacy policy and terms of service live
- [ ] Cookie consent (if required)

---

## 8. Key Risks & Mitigation

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| SEBI regulatory scrutiny | Medium | Add clear disclaimers; avoid "advice" language |
| yfinance deprecated / rate-limited | Medium | Build abstraction layer; add Zerodha Kite API as backup |
| Low conversion free → paid | High | Ensure trade parameters (entry/target/SL) are Pro-only |
| Competitors copy the model | Medium | Speed + brand trust + track record are moat |
| LLM API cost at scale | Medium | Cache reasoning; only generate for BUY opportunities |
| Bad outcome damages trust | Low | Show losses honestly; track record builds long-term trust |

---

## 9. Success Milestones

| Milestone | Target Date | Metric |
|-----------|------------|--------|
| Hackathon demo working | Week 1 | System completes end-to-end scan |
| Beta launch | Month 2 | 100 beta users |
| First ₹1 lakh MRR | Month 4 | ~200 Pro users |
| 1,000 active free users | Month 4 | DAU tracking |
| 70%+ backtest win rate | Ongoing | System accuracy metric |
| Media coverage (MoneyControl, ET Markets) | Month 6 | 1+ article |
| Broker partnership (1st) | Month 9 | Integration live |
| 10,000 active users | Month 12 | Growth milestone |

---

## 10. Team Needs (Post-Hackathon)

| Role | Priority | Why |
|------|----------|-----|
| Full-stack developer | Immediate | Scale the codebase |
| SEBI Research Analyst | Month 3 | For personalized advice features |
| Growth / community manager | Month 2 | Handle the content + community flywheel |
| Data scientist | Month 4 | Additional signal types + ML experimentation |

---

*Last updated: 2026-03-25 | Version: 1.0*
