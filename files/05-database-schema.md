# 05 — Database Schema

## AlphaHunter AI — Opportunity & Decision Engine

---

## 1. Overview

This document defines the complete database schema for AlphaHunter AI. The primary database is **PostgreSQL** (production) with **SQLite** supported for local development. The schema is managed via **SQLAlchemy ORM** with **Alembic** for migrations.

---

## 2. Entity Relationship Overview

```
stocks ──────────────────────────────────────────────┐
   │                                                  │
   │  1:N                                             │
   ▼                                                  │
scan_results ──────────────────────────────────────  │
   │                                                  │
   │  1:1                                             │
   ▼                                                  │
decisions ─────────────────────────────────────────  │
   │                                                  │
   │  1:1                                             │
   ▼                                                  │
decision_outcomes ─────────────────────────────────  │
                                                      │
market_data_cache ─────────────────────────────────  │
bulk_deals ────────────────────────────────────────  │
watchlist_items ───────────────────────────────────  │
alerts ─────────────────────────────────────────────  │
scan_runs ──────────────────────────────────────────  │
audit_logs ─────────────────────────────────────────  │
```

---

## 3. Table Definitions

### 3.1 `stocks`

Master list of all NSE stocks tracked by the system.

```sql
CREATE TABLE stocks (
    id              SERIAL PRIMARY KEY,
    symbol          VARCHAR(20) NOT NULL UNIQUE,
    name            VARCHAR(200) NOT NULL,
    sector          VARCHAR(100),
    market_cap_cr   DECIMAL(15, 2),        -- in crores INR
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    nse_code        VARCHAR(20),
    bse_code        VARCHAR(20),
    isin            VARCHAR(12),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_stocks_symbol ON stocks(symbol);
CREATE INDEX idx_stocks_sector ON stocks(sector);
```

**Sample data:**
```sql
INSERT INTO stocks (symbol, name, sector) VALUES
  ('INFY', 'Infosys Ltd', 'IT'),
  ('TCS', 'Tata Consultancy Services', 'IT'),
  ('RELIANCE', 'Reliance Industries Ltd', 'Energy'),
  ('HDFCBANK', 'HDFC Bank Ltd', 'Banking'),
  ('TATASTEEL', 'Tata Steel Ltd', 'Metals');
```

---

### 3.2 `scan_runs`

Tracks each execution of the full market scan pipeline.

```sql
CREATE TABLE scan_runs (
    id              SERIAL PRIMARY KEY,
    run_id          UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    triggered_by    VARCHAR(20) NOT NULL DEFAULT 'scheduler',  -- 'scheduler' | 'manual'
    started_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMP,
    status          VARCHAR(20) NOT NULL DEFAULT 'running',    -- 'running' | 'completed' | 'failed'
    stocks_scanned  INTEGER DEFAULT 0,
    signals_found   INTEGER DEFAULT 0,
    error_message   TEXT,
    duration_secs   DECIMAL(6, 2)
);

CREATE INDEX idx_scan_runs_started_at ON scan_runs(started_at DESC);
CREATE INDEX idx_scan_runs_status ON scan_runs(status);
```

---

### 3.3 `market_data_cache`

Caches fetched OHLCV + volume data to reduce redundant API calls.

```sql
CREATE TABLE market_data_cache (
    id              SERIAL PRIMARY KEY,
    symbol          VARCHAR(20) NOT NULL,
    data_type       VARCHAR(30) NOT NULL,  -- 'ohlcv_live' | 'ohlcv_20d' | 'ohlcv_2yr' | 'bulk_deals'
    data_json       JSONB NOT NULL,
    fetched_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMP NOT NULL,
    source          VARCHAR(50) DEFAULT 'yfinance'
);

CREATE INDEX idx_mdc_symbol_type ON market_data_cache(symbol, data_type);
CREATE INDEX idx_mdc_expires_at ON market_data_cache(expires_at);
```

**TTL rules:**
- `ohlcv_live`: 5 minutes
- `ohlcv_20d`: 15 minutes
- `ohlcv_2yr`: 24 hours
- `bulk_deals`: 6 hours

---

### 3.4 `bulk_deals`

Stores NSE bulk deal activity fetched from NSE's public feed.

```sql
CREATE TABLE bulk_deals (
    id              SERIAL PRIMARY KEY,
    symbol          VARCHAR(20) NOT NULL,
    deal_date       DATE NOT NULL,
    client_name     VARCHAR(200),
    deal_type       VARCHAR(10),           -- 'BUY' | 'SELL'
    quantity        BIGINT,
    price           DECIMAL(10, 2),
    exchange        VARCHAR(10) DEFAULT 'NSE',
    fetched_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_bulk_deal UNIQUE (symbol, deal_date, client_name, deal_type)
);

CREATE INDEX idx_bulk_deals_symbol ON bulk_deals(symbol);
CREATE INDEX idx_bulk_deals_date ON bulk_deals(deal_date DESC);
```

---

### 3.5 `scan_results`

Stores the signal output for each stock per scan run.

```sql
CREATE TABLE scan_results (
    id              SERIAL PRIMARY KEY,
    scan_run_id     INTEGER NOT NULL REFERENCES scan_runs(id) ON DELETE CASCADE,
    symbol          VARCHAR(20) NOT NULL,
    scanned_at      TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Price data at time of scan
    price           DECIMAL(10, 2),
    volume_today    BIGINT,
    volume_avg_20d  BIGINT,
    volume_ratio    DECIMAL(5, 2),

    -- Signal flags
    breakout_triggered      BOOLEAN NOT NULL DEFAULT FALSE,
    volume_spike_triggered  BOOLEAN NOT NULL DEFAULT FALSE,
    bulk_deal_triggered     BOOLEAN NOT NULL DEFAULT FALSE,

    -- Signal details (JSON for flexibility)
    breakout_details        JSONB,
    volume_spike_details    JSONB,
    bulk_deal_details       JSONB,

    -- Composite
    signal_count            INTEGER NOT NULL DEFAULT 0,
    composite_score         DECIMAL(5, 4),

    -- LLM reasoning
    reasoning_text          TEXT,
    reasoning_generated_at  TIMESTAMP,

    -- Backtest
    backtest_matches        INTEGER,
    backtest_success_rate   DECIMAL(5, 2),
    backtest_avg_return     DECIMAL(6, 3),
    backtest_worst_case     DECIMAL(6, 3),
    backtest_best_case      DECIMAL(6, 3),
    backtest_cases_json     JSONB,

    CONSTRAINT uq_scan_result UNIQUE (scan_run_id, symbol)
);

CREATE INDEX idx_scan_results_run_id ON scan_results(scan_run_id);
CREATE INDEX idx_scan_results_symbol ON scan_results(symbol);
CREATE INDEX idx_scan_results_composite ON scan_results(composite_score DESC);
```

---

### 3.6 `decisions`

The core decision table — stores every BUY/WATCH/AVOID recommendation.

```sql
CREATE TABLE decisions (
    id              SERIAL PRIMARY KEY,
    decision_id     UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    scan_result_id  INTEGER REFERENCES scan_results(id),
    symbol          VARCHAR(20) NOT NULL,
    decided_at      TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Action
    action          VARCHAR(10) NOT NULL,   -- 'BUY' | 'WATCH' | 'AVOID'
    confidence      DECIMAL(5, 2) NOT NULL, -- 0.00 to 100.00

    -- Trade parameters (populated for BUY only)
    entry_price     DECIMAL(10, 2),
    target_price    DECIMAL(10, 2),
    stop_loss       DECIMAL(10, 2),
    rr_ratio        DECIMAL(5, 2),

    -- Score breakdown (for confidence transparency)
    score_signal    DECIMAL(5, 4),
    score_backtest  DECIMAL(5, 4),
    score_composite DECIMAL(5, 4),

    -- Full frozen snapshot of all data at decision time
    snapshot_json   JSONB NOT NULL,

    -- Outcome tracking
    outcome_measured        BOOLEAN NOT NULL DEFAULT FALSE,
    outcome_measure_at      TIMESTAMP,  -- scheduled for T+5
    outcome_exit_price      DECIMAL(10, 2),
    outcome_return_pct      DECIMAL(6, 3),
    outcome_result          VARCHAR(10),  -- 'profit' | 'loss' | 'neutral' | 'pending'
    outcome_measured_at     TIMESTAMP
);

CREATE INDEX idx_decisions_symbol ON decisions(symbol);
CREATE INDEX idx_decisions_decided_at ON decisions(decided_at DESC);
CREATE INDEX idx_decisions_action ON decisions(action);
CREATE INDEX idx_decisions_outcome ON decisions(outcome_result);
```

---

### 3.7 `watchlist_items`

User's tracked stocks.

```sql
CREATE TABLE watchlist_items (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(50) NOT NULL DEFAULT 'default',  -- future multi-user
    symbol          VARCHAR(20) NOT NULL,
    added_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    notes           TEXT,
    CONSTRAINT uq_watchlist_item UNIQUE (user_id, symbol)
);

CREATE INDEX idx_watchlist_user ON watchlist_items(user_id);
```

---

### 3.8 `alerts`

Stores triggered alert notifications.

```sql
CREATE TABLE alerts (
    id              SERIAL PRIMARY KEY,
    alert_id        UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    symbol          VARCHAR(20) NOT NULL,
    decision_id     UUID REFERENCES decisions(decision_id),
    alert_type      VARCHAR(30) NOT NULL,  -- 'signal_triggered' | 'outcome_available'
    message         TEXT NOT NULL,
    confidence      DECIMAL(5, 2),
    action          VARCHAR(10),
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alerts_is_read ON alerts(is_read);
CREATE INDEX idx_alerts_created_at ON alerts(created_at DESC);
```

---

### 3.9 `system_settings`

Key-value store for application configuration and user preferences.

```sql
CREATE TABLE system_settings (
    id              SERIAL PRIMARY KEY,
    key             VARCHAR(100) NOT NULL UNIQUE,
    value           TEXT NOT NULL,
    description     TEXT,
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Default values
INSERT INTO system_settings (key, value, description) VALUES
  ('alert_confidence_threshold', '65', 'Minimum confidence to trigger alert'),
  ('breakout_lookback_days', '30', 'Days to look back for resistance level'),
  ('volume_spike_threshold', '2.0', 'Volume multiplier to trigger spike signal'),
  ('scan_interval_minutes', '15', 'Minutes between automated scans'),
  ('backtest_lookback_years', '2', 'Years of history for backtesting'),
  ('bulk_deal_lookback_days', '5', 'Days to look back for bulk deals');
```

---

### 3.10 `audit_logs`

System-wide event and error log for operations and debugging.

```sql
CREATE TABLE audit_logs (
    id              SERIAL PRIMARY KEY,
    timestamp       TIMESTAMP NOT NULL DEFAULT NOW(),
    level           VARCHAR(10) NOT NULL,   -- 'INFO' | 'WARNING' | 'ERROR'
    module          VARCHAR(50) NOT NULL,   -- 'data_agent' | 'signal_agent' | etc.
    event           VARCHAR(100) NOT NULL,
    detail          TEXT,
    symbol          VARCHAR(20),
    scan_run_id     INTEGER,
    duration_ms     INTEGER
);

CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_level ON audit_logs(level);
CREATE INDEX idx_audit_logs_module ON audit_logs(module);
```

---

## 4. Views

### 4.1 `v_latest_opportunities`

Convenience view for the most recent scan's opportunities.

```sql
CREATE OR REPLACE VIEW v_latest_opportunities AS
SELECT
    sr.symbol,
    s.name,
    sr.price,
    sr.volume_ratio,
    sr.breakout_triggered,
    sr.volume_spike_triggered,
    sr.bulk_deal_triggered,
    sr.signal_count,
    sr.composite_score,
    sr.reasoning_text,
    sr.backtest_success_rate,
    sr.backtest_avg_return,
    d.action,
    d.confidence,
    d.entry_price,
    d.target_price,
    d.stop_loss,
    d.rr_ratio,
    sr.scanned_at
FROM scan_results sr
JOIN scan_runs run ON sr.scan_run_id = run.id
LEFT JOIN decisions d ON d.scan_result_id = sr.id
LEFT JOIN stocks s ON s.symbol = sr.symbol
WHERE run.id = (
    SELECT id FROM scan_runs
    WHERE status = 'completed'
    ORDER BY completed_at DESC
    LIMIT 1
)
AND sr.signal_count > 0
ORDER BY sr.composite_score DESC;
```

---

### 4.2 `v_decision_track_record`

Decision history with outcomes for the track record dashboard.

```sql
CREATE OR REPLACE VIEW v_decision_track_record AS
SELECT
    d.decision_id,
    d.symbol,
    d.decided_at,
    d.action,
    d.confidence,
    d.entry_price,
    d.target_price,
    d.stop_loss,
    d.outcome_result,
    d.outcome_return_pct,
    d.outcome_measured_at,
    CASE
        WHEN d.outcome_result = 'profit' THEN TRUE
        WHEN d.outcome_result = 'loss' THEN FALSE
        ELSE NULL
    END AS is_profitable
FROM decisions d
WHERE d.action = 'BUY'
ORDER BY d.decided_at DESC;
```

---

## 5. Indexes Summary

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| stocks | idx_stocks_symbol | symbol | Fast lookup |
| scan_runs | idx_scan_runs_started_at | started_at DESC | Recent scans |
| market_data_cache | idx_mdc_symbol_type | symbol, data_type | Cache hit check |
| market_data_cache | idx_mdc_expires_at | expires_at | Cache expiry cleanup |
| scan_results | idx_scan_results_composite | composite_score DESC | Ranked results |
| decisions | idx_decisions_decided_at | decided_at DESC | History queries |
| decisions | idx_decisions_action | action | Filter by BUY/WATCH/AVOID |
| alerts | idx_alerts_is_read | is_read | Unread count |
| audit_logs | idx_audit_logs_timestamp | timestamp DESC | Log queries |

---

## 6. Migration Strategy

- Migrations managed with **Alembic**
- Each migration file: `YYYYMMDD_HHMMSS_description.py`
- Migration commands:
  ```bash
  alembic upgrade head       # Apply all migrations
  alembic downgrade -1       # Rollback one migration
  alembic revision --autogenerate -m "add bulk_deals table"
  ```

---

## 7. Backup & Retention

| Data | Retention | Backup Frequency |
|------|-----------|-----------------|
| `decisions` | Indefinite | Daily |
| `scan_results` | 90 days | Weekly |
| `market_data_cache` | TTL-based auto-expiry | None needed |
| `audit_logs` | 30 days | None |
| `bulk_deals` | 30 days | None |

---

*Last updated: 2026-03-25 | Version: 1.0*
