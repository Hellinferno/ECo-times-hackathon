# 03 — Information Architecture

## AlphaHunter AI — Opportunity & Decision Engine

---

## 1. Overview

This document defines the full information architecture (IA) of AlphaHunter AI — how content, features, and navigation are structured across the application. It covers site maps, navigation hierarchy, page inventory, and content models.

---

## 2. Application Sections (Top-Level)

```
AlphaHunter AI
├── Dashboard (Home)
├── Market Scanner
├── Stock Detail
├── Past Decisions (Audit Trail)
├── Watchlist
├── Alerts
└── Settings
    ├── Alert Preferences
    ├── Signal Preferences
    └── Account
```

---

## 3. Navigation Structure

### 3.1 Primary Navigation (Sidebar / Bottom Nav)

| Icon | Label | Route | Description |
|------|-------|--------|-------------|
| 🏠 | Dashboard | `/` | Summary of today's market pulse |
| 🔍 | Scanner | `/scanner` | Run market scan, view opportunities |
| 📈 | Watchlist | `/watchlist` | Tracked stocks + signal status |
| 📜 | History | `/history` | Past decisions and outcomes |
| 🔔 | Alerts | `/alerts` | Notification center |
| ⚙️ | Settings | `/settings` | Preferences and configuration |

### 3.2 Secondary Navigation (Contextual)

- Stock Detail page: tabs for Signal / Reasoning / Backtest / Action / Chart
- History page: filters for date range, outcome, stock
- Settings page: sub-tabs for Alerts / Signals / Account

---

## 4. Page Inventory

### 4.1 Dashboard — `/`

**Purpose:** Quick overview of what matters today

**Content Blocks:**
- Market Pulse Summary (number of signals detected today)
- Top 3 Opportunities (preview cards)
- Watchlist Status (quick view — any signals on watched stocks?)
- Last Scan Timestamp
- Quick Action: "Scan Now" button

---

### 4.2 Market Scanner — `/scanner`

**Purpose:** Run a full market scan and view ranked opportunities

**Content Blocks:**
- Scan Controls (trigger button, last scan time)
- Opportunity List (ranked cards)
- Filter Bar (by Action: BUY / WATCH / AVOID; by Signal type)
- Scan Statistics (stocks scanned, opportunities found, scan duration)
- Empty / Loading States

**Card Components (per opportunity):**
```
[Stock Symbol + Name]
[Signal Tags: Breakout | Volume Spike | Bulk Deal]
[Action Badge: BUY / WATCH / AVOID]
[Confidence %]
[→ View Details]
```

---

### 4.3 Stock Detail — `/stock/:symbol`

**Purpose:** Full decision breakdown for a single stock

**Tab Structure:**

#### Tab 1 — Overview
- Current Price, Day Change, Volume
- Active Signal Summary
- AI Reasoning (LLM explanation paragraph)
- Final Recommendation Card (BUY/WATCH/AVOID + confidence)

#### Tab 2 — Signals
- Signal cards: Breakout, Volume Spike, Bulk Deal
- Each signal: data values, threshold vs actual, strength indicator

#### Tab 3 — Backtest
- Similar past signals table (date, return, outcome)
- Success rate + average return summary
- Methodology note

#### Tab 4 — Trade Plan
- Entry Price
- Target Price
- Stop-Loss
- Risk:Reward Ratio
- Confidence Breakdown Chart

#### Tab 5 — Chart
- Price chart (6 months)
- Past signal markers
- Volume bar overlay
- Resistance/support levels marked

---

### 4.4 Past Decisions — `/history`

**Purpose:** Audit trail of all past system recommendations

**Content Blocks:**
- Overall Stats (Win Rate %, Total Decisions, Avg Return)
- Filter Bar (date range, stock, outcome: profit/loss/pending)
- Decision Log Table:
  ```
  Date | Stock | Signal | Action | Confidence | T+5 Return | Outcome
  ```
- Export to CSV button

**Decision Detail View (modal or page):**
- Full snapshot of signal, reasoning, backtest, action
- Price chart from decision date forward
- Outcome annotation

---

### 4.5 Watchlist — `/watchlist`

**Purpose:** Monitor stocks the user has added

**Content Blocks:**
- Watchlist cards (up to 20 stocks)
- Per card: symbol, last signal, last scan time, action status
- "Add Stock" search input
- Sort: by signal strength, alphabetical, last updated

---

### 4.6 Alerts — `/alerts`

**Purpose:** Notification inbox

**Content Blocks:**
- Unread alert count badge
- Alert list: timestamp, stock, signal summary, confidence
- Click-through to stock detail
- Mark all as read
- Clear alerts

---

### 4.7 Settings — `/settings`

#### Alert Preferences
- Enable/disable notifications
- Minimum confidence threshold slider (default: 65%)
- Alert types to receive (Breakout, Volume, Bulk Deal)

#### Signal Preferences
- Breakout sensitivity (lookback period: 20 / 30 / 60 days)
- Volume spike threshold (1.5x / 2x / 3x)
- Fundamental signals: toggle Bulk Deal on/off

#### Account
- Display name
- Email (for future email alerts)
- Theme (Dark / Light)

---

## 5. Content Model

### 5.1 Opportunity Object

```json
{
  "symbol": "INFY",
  "name": "Infosys Ltd",
  "price": 1502.45,
  "change_pct": 2.3,
  "signals": ["breakout", "volume_spike"],
  "action": "BUY",
  "confidence": 78,
  "entry": 1480,
  "target": 1580,
  "stop_loss": 1420,
  "rr_ratio": 2.3,
  "reasoning": "Stock crossed ₹1,500 resistance (30-day level) with 2.3x volume...",
  "backtest": {
    "matches": 5,
    "success_rate": 80,
    "avg_return": 5.2,
    "worst_case": -3.1
  },
  "scanned_at": "2026-03-25T09:45:00Z"
}
```

---

### 5.2 Signal Object

```json
{
  "type": "breakout",
  "triggered": true,
  "resistance_level": 1500,
  "current_price": 1502.45,
  "pct_above": 0.16,
  "lookback_days": 30
}
```

```json
{
  "type": "volume_spike",
  "triggered": true,
  "today_volume": 4600000,
  "avg_volume_20d": 2000000,
  "ratio": 2.3
}
```

```json
{
  "type": "bulk_deal",
  "triggered": true,
  "buyer": "Axis Mutual Fund",
  "quantity": 500000,
  "price": 1495,
  "date": "2026-03-22"
}
```

---

### 5.3 Decision Log Object

```json
{
  "id": "dec_20260325_INFY",
  "symbol": "INFY",
  "action": "BUY",
  "confidence": 78,
  "decided_at": "2026-03-25T09:45:00Z",
  "entry": 1480,
  "target": 1580,
  "stop_loss": 1420,
  "outcome": {
    "measured_at": "2026-03-30T15:30:00Z",
    "exit_price": 1551,
    "return_pct": 4.8,
    "result": "profit"
  },
  "snapshot": { ... }
}
```

---

## 6. User Flow Diagrams

### 6.1 Primary Flow — Find and Act on an Opportunity

```
[Dashboard]
    ↓ Click "Scan Now"
[Scanner — Loading]
    ↓ Results loaded
[Opportunity List]
    ↓ Click a stock
[Stock Detail — Overview Tab]
    ↓ Read reasoning
[Trade Plan Tab]
    ↓ Note Entry / Target / Stop-Loss
[User executes trade externally]
    ↓ (T+5 days)
[History — Outcome updated]
```

---

### 6.2 Secondary Flow — Evaluate Track Record

```
[History Page]
    ↓ View overall win rate
[Decision log table]
    ↓ Click a past decision
[Decision Detail View]
    ↓ Review snapshot
[Chart — see price after decision]
[User builds trust in system]
```

---

### 6.3 Alert Flow

```
[Background scan runs every 15 min]
    ↓ Signal triggered with confidence ≥ threshold
[Alert created in system]
    ↓ In-app notification pushed
[User sees badge on Alerts nav]
    ↓ Opens Alerts
[Clicks alert → Stock Detail]
```

---

## 7. Information Hierarchy Summary

```
Level 1: Navigation Sections (6 top-level areas)
Level 2: Pages within each section
Level 3: Tabs / sub-sections within pages
Level 4: Cards / components within tabs
Level 5: Data fields within components
```

---

## 8. Accessibility & Discoverability Notes

- All key actions reachable within 3 clicks from Dashboard
- Scan results appear without requiring user to configure anything
- Confidence score and action are always the most visually prominent elements
- Backtest data is always one tab away from the main recommendation
- Empty states include a clear next-action CTA

---

*Last updated: 2026-03-25 | Version: 1.0*
