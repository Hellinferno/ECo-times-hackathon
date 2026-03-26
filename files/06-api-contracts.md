# 06 — API Contracts

## AlphaHunter AI — Opportunity & Decision Engine

---

## 1. Overview

This document defines the complete REST API contracts for AlphaHunter AI's backend. The API is built with **FastAPI** and follows REST conventions. All responses use `application/json`. Base URL: `http://localhost:8000/api` (dev) or `https://api.alphahunter.ai/api` (prod).

---

## 2. Global Conventions

### 2.1 Request Headers

```
Content-Type: application/json
Accept: application/json
```

### 2.2 Standard Response Envelope

All endpoints return a standard response envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "timestamp": "2026-03-25T09:45:00Z",
    "version": "1.0"
  }
}
```

On error:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "SCAN_IN_PROGRESS",
    "message": "A scan is already running. Please wait."
  },
  "meta": {
    "timestamp": "2026-03-25T09:45:00Z"
  }
}
```

### 2.3 HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Success |
| 201 | Resource created |
| 400 | Bad request (validation error) |
| 404 | Resource not found |
| 409 | Conflict (e.g., scan already running) |
| 500 | Internal server error |

---

## 3. Scanner Endpoints

### `POST /api/scan`

Triggers a full market scan across all active stocks.

**Request Body:**
```json
{
  "mode": "full",           // "full" | "watchlist_only"
  "symbols": null           // null = all stocks, or ["INFY", "TCS"] for targeted
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "scan_run_id": "a1b2c3d4-...",
    "status": "running",
    "started_at": "2026-03-25T09:45:00Z",
    "stocks_queued": 105,
    "estimated_duration_secs": 45
  }
}
```

**Response 409 (scan already running):**
```json
{
  "success": false,
  "error": {
    "code": "SCAN_IN_PROGRESS",
    "message": "A scan is already running. Please wait.",
    "active_scan_id": "x9y8z7w6-..."
  }
}
```

---

### `GET /api/scan/{scan_run_id}/status`

Poll scan progress.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "scan_run_id": "a1b2c3d4-...",
    "status": "completed",
    "started_at": "2026-03-25T09:45:00Z",
    "completed_at": "2026-03-25T09:45:47Z",
    "stocks_scanned": 105,
    "signals_found": 7,
    "duration_secs": 47.3
  }
}
```

---

### `GET /api/scan/latest`

Returns metadata for the most recently completed scan.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "scan_run_id": "a1b2c3d4-...",
    "status": "completed",
    "completed_at": "2026-03-25T09:45:47Z",
    "stocks_scanned": 105,
    "signals_found": 7
  }
}
```

---

## 4. Opportunities Endpoints

### `GET /api/opportunities`

Returns ranked list of opportunities from the latest completed scan.

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `action` | string | null | Filter: `BUY` / `WATCH` / `AVOID` |
| `signal` | string | null | Filter: `breakout` / `volume_spike` / `bulk_deal` |
| `min_confidence` | float | 0 | Minimum confidence threshold |
| `limit` | int | 20 | Max results |
| `offset` | int | 0 | Pagination offset |

**Response 200:**
```json
{
  "success": true,
  "data": {
    "scan_run_id": "a1b2c3d4-...",
    "scanned_at": "2026-03-25T09:45:47Z",
    "total": 7,
    "opportunities": [
      {
        "symbol": "INFY",
        "name": "Infosys Ltd",
        "price": 1502.45,
        "change_pct": 2.3,
        "action": "BUY",
        "confidence": 78.0,
        "signal_count": 3,
        "signals": ["breakout", "volume_spike", "bulk_deal"],
        "composite_score": 0.82
      },
      ...
    ]
  }
}
```

---

## 5. Stock Detail Endpoints

### `GET /api/stock/{symbol}`

Returns full analysis detail for a single stock.

**Path Parameters:**
- `symbol` (string, required): NSE stock symbol (e.g., `INFY`)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "symbol": "INFY",
    "name": "Infosys Ltd",
    "sector": "IT",
    "price": 1502.45,
    "change_pct": 2.3,
    "volume_today": 4600000,
    "volume_avg_20d": 2000000,
    "volume_ratio": 2.3,
    "signals": {
      "breakout": {
        "triggered": true,
        "resistance_level": 1500.00,
        "current_price": 1502.45,
        "pct_above": 0.16,
        "lookback_days": 30,
        "strength": 0.72
      },
      "volume_spike": {
        "triggered": true,
        "today_volume": 4600000,
        "avg_volume_20d": 2000000,
        "ratio": 2.3,
        "strength": 0.85
      },
      "bulk_deal": {
        "triggered": true,
        "buyer": "Axis Mutual Fund",
        "deal_type": "BUY",
        "quantity": 500000,
        "price": 1495.00,
        "date": "2026-03-22",
        "strength": 0.90
      }
    },
    "reasoning": "Infosys crossed its 30-day resistance of ₹1,500 at ₹1,502, a level that has held for 4 weeks. Volume today reached 4.6M shares — 2.3x the 20-day average — indicating strong institutional demand. Axis Mutual Fund executed a bulk purchase of 500,000 shares at ₹1,495 on March 22, confirming smart-money accumulation.",
    "backtest": {
      "matches": 5,
      "success_rate": 80.0,
      "avg_return_pct": 5.2,
      "worst_case_pct": -3.1,
      "best_case_pct": 9.8,
      "cases": [
        { "date": "2025-11-10", "return_pct": 6.1, "profitable": true },
        { "date": "2025-08-22", "return_pct": 4.8, "profitable": true },
        { "date": "2025-05-14", "return_pct": -3.1, "profitable": false },
        { "date": "2025-02-07", "return_pct": 9.8, "profitable": true },
        { "date": "2024-10-30", "return_pct": 5.5, "profitable": true }
      ]
    },
    "decision": {
      "action": "BUY",
      "confidence": 78.0,
      "entry_price": 1502.45,
      "target_price": 1580.00,
      "stop_loss": 1455.00,
      "rr_ratio": 2.3,
      "score_breakdown": {
        "signal_score": 0.82,
        "backtest_score": 0.80,
        "composite_score": 0.78
      }
    },
    "scanned_at": "2026-03-25T09:45:00Z"
  }
}
```

**Response 404:**
```json
{
  "success": false,
  "error": {
    "code": "STOCK_NOT_FOUND",
    "message": "Stock symbol 'XYZ' not found in system"
  }
}
```

---

### `GET /api/stock/{symbol}/chart`

Returns OHLCV data for chart rendering.

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `period` | string | `6mo` | `1mo` / `3mo` / `6mo` / `1yr` / `2yr` |
| `interval` | string | `1d` | `1d` / `1wk` |

**Response 200:**
```json
{
  "success": true,
  "data": {
    "symbol": "INFY",
    "period": "6mo",
    "interval": "1d",
    "ohlcv": [
      {
        "date": "2025-09-25",
        "open": 1380.00,
        "high": 1395.50,
        "low": 1375.20,
        "close": 1392.10,
        "volume": 1850000
      },
      ...
    ],
    "signal_markers": [
      {
        "date": "2025-11-10",
        "type": "breakout",
        "return_pct": 6.1,
        "profitable": true
      }
    ],
    "resistance_level": 1500.00,
    "support_level": 1420.00
  }
}
```

---

## 6. Decision History Endpoints

### `GET /api/history`

Returns paginated list of past decisions.

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `action` | string | null | Filter by BUY/WATCH/AVOID |
| `outcome` | string | null | `profit` / `loss` / `neutral` / `pending` |
| `symbol` | string | null | Filter by stock symbol |
| `from_date` | date | 30 days ago | Start date (YYYY-MM-DD) |
| `to_date` | date | today | End date (YYYY-MM-DD) |
| `limit` | int | 50 | Max results |
| `offset` | int | 0 | Pagination |

**Response 200:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_decisions": 42,
      "buy_decisions": 28,
      "win_rate_pct": 71.4,
      "avg_return_pct": 3.8
    },
    "decisions": [
      {
        "decision_id": "d1e2f3a4-...",
        "symbol": "INFY",
        "decided_at": "2026-03-25T09:45:00Z",
        "action": "BUY",
        "confidence": 78.0,
        "entry_price": 1480.00,
        "target_price": 1580.00,
        "stop_loss": 1420.00,
        "outcome_result": "profit",
        "outcome_return_pct": 4.8,
        "outcome_measured_at": "2026-03-30T15:30:00Z"
      },
      ...
    ],
    "pagination": {
      "total": 42,
      "limit": 50,
      "offset": 0
    }
  }
}
```

---

### `GET /api/history/{decision_id}`

Returns full detail replay for a single past decision.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "decision_id": "d1e2f3a4-...",
    "symbol": "INFY",
    "decided_at": "2026-03-20T09:30:00Z",
    "action": "BUY",
    "confidence": 78.0,
    "entry_price": 1480.00,
    "target_price": 1580.00,
    "stop_loss": 1420.00,
    "outcome": {
      "result": "profit",
      "exit_price": 1551.00,
      "return_pct": 4.8,
      "measured_at": "2026-03-25T15:30:00Z"
    },
    "snapshot": {
      "signals": { ... },           // as they were at decision time
      "reasoning": "...",
      "backtest": { ... }
    }
  }
}
```

---

### `GET /api/history/export`

Exports decision history as CSV.

**Query Parameters:** Same as `GET /api/history` (for date range filtering)

**Response 200:**
```
Content-Type: text/csv
Content-Disposition: attachment; filename="alphahunter_decisions_2026-03-25.csv"

decision_id,symbol,decided_at,action,confidence,entry_price,target_price,stop_loss,outcome_result,outcome_return_pct
d1e2f3a4,...,INFY,2026-03-25T09:45:00Z,BUY,78.0,1480.00,1580.00,1420.00,profit,4.8
...
```

---

## 7. Watchlist Endpoints

### `GET /api/watchlist`

Returns the user's watchlist.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "count": 3,
    "items": [
      {
        "symbol": "INFY",
        "name": "Infosys Ltd",
        "added_at": "2026-03-20T10:00:00Z",
        "current_price": 1502.45,
        "latest_signal": {
          "action": "BUY",
          "confidence": 78.0,
          "scanned_at": "2026-03-25T09:45:00Z"
        }
      },
      ...
    ]
  }
}
```

---

### `POST /api/watchlist/{symbol}`

Adds a stock to the watchlist.

**Response 201:**
```json
{
  "success": true,
  "data": {
    "symbol": "INFY",
    "added_at": "2026-03-25T11:00:00Z"
  }
}
```

**Response 409 (already in watchlist):**
```json
{
  "success": false,
  "error": {
    "code": "ALREADY_IN_WATCHLIST",
    "message": "INFY is already in your watchlist"
  }
}
```

---

### `DELETE /api/watchlist/{symbol}`

Removes a stock from the watchlist.

**Response 200:**
```json
{
  "success": true,
  "data": { "removed": true }
}
```

---

## 8. Alerts Endpoints

### `GET /api/alerts`

Returns alerts.

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `is_read` | bool | null | Filter by read status |
| `limit` | int | 20 | Max results |

**Response 200:**
```json
{
  "success": true,
  "data": {
    "unread_count": 2,
    "alerts": [
      {
        "alert_id": "a1b2c3d4-...",
        "symbol": "INFY",
        "alert_type": "signal_triggered",
        "message": "INFY triggered BUY signal — Confidence: 78%",
        "action": "BUY",
        "confidence": 78.0,
        "is_read": false,
        "created_at": "2026-03-25T09:46:00Z"
      },
      ...
    ]
  }
}
```

---

### `POST /api/alerts/mark-read`

Marks one or all alerts as read.

**Request Body:**
```json
{ "alert_ids": ["a1b2c3d4-..."] }  // or "all" to mark everything
```

**Response 200:**
```json
{ "success": true, "data": { "marked_count": 1 } }
```

---

## 9. Settings Endpoints

### `GET /api/settings`

Returns current system settings.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "alert_confidence_threshold": 65,
    "breakout_lookback_days": 30,
    "volume_spike_threshold": 2.0,
    "scan_interval_minutes": 15,
    "bulk_deal_lookback_days": 5
  }
}
```

---

### `PATCH /api/settings`

Updates one or more settings.

**Request Body:**
```json
{
  "alert_confidence_threshold": 70,
  "volume_spike_threshold": 2.5
}
```

**Response 200:**
```json
{ "success": true, "data": { "updated_keys": ["alert_confidence_threshold", "volume_spike_threshold"] } }
```

---

## 10. Health Check

### `GET /api/health`

System health status for monitoring.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "database": "connected",
    "redis": "connected",
    "last_scan": "2026-03-25T09:45:47Z",
    "data_feeds": {
      "yfinance": "ok",
      "nse_bulk_deals": "ok"
    },
    "version": "1.0.0"
  }
}
```

---

*Last updated: 2026-03-25 | Version: 1.0*
