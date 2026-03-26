# 08 — Computation Engine Spec

## AlphaHunter AI — Signal Detection, Scoring & Decision Logic

---

## 1. Overview

This document defines the **exact mathematical logic** for every computation in AlphaHunter AI. It covers signal detection formulas, scoring models, confidence calculation, trade parameter generation, and backtesting methodology. Every number produced by the system must trace back to a formula in this document.

---

## 2. Signal Detection Algorithms

### 2.1 Breakout Signal

**Definition:** Stock price has crossed above a significant resistance level with meaningful momentum.

**Formula:**
```
resistance_level = max(close_prices[-N:])   where N = breakout_lookback_days (default: 30)
breakout_triggered = current_price > resistance_level
pct_above = (current_price - resistance_level) / resistance_level * 100
```

**Strength Score:**
```
if not breakout_triggered: strength = 0.0
else:
    # Strength increases with how far above resistance we are
    # Capped at 5% above = max strength
    raw_strength = min(pct_above / 5.0, 1.0)
    
    # Bonus for fresh breakout (within last 1 day)
    recency_bonus = 0.15 if breakout_age_days <= 1 else 0.0
    
    strength = min(raw_strength + recency_bonus, 1.0)
```

**Tunable Parameters:**

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `breakout_lookback_days` | 30 | 20–60 | Longer = stronger resistance level |
| `min_pct_above` | 0.0 | 0–2% | Minimum distance above resistance |

**Edge Cases:**
- If lookback window has fewer than 5 trading days of data → signal not evaluated (returns None)
- If resistance level equals current price exactly → breakout NOT triggered (must be strictly above)

---

### 2.2 Volume Spike Signal

**Definition:** Today's trading volume is significantly above the recent average, indicating unusual activity.

**Formula:**
```
avg_volume_20d = mean(volume[-20:])    # 20-day simple moving average of volume
volume_ratio = today_volume / avg_volume_20d
volume_spike_triggered = volume_ratio >= volume_spike_threshold (default: 2.0)
```

**Strength Score:**
```
if not volume_spike_triggered: strength = 0.0
else:
    # Normalize: 2x = 0.5 strength, 4x = 1.0 strength (linear scale between threshold and 4x)
    threshold = volume_spike_threshold  # e.g., 2.0
    max_ratio = 4.0
    strength = min((volume_ratio - threshold) / (max_ratio - threshold), 1.0)
    strength = max(strength, 0.1)   # Minimum 0.1 if triggered
```

**Tunable Parameters:**

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `volume_spike_threshold` | 2.0 | 1.5–3.0 | Higher = fewer but stronger signals |
| `volume_avg_period` | 20 | 10–30 | Window for average calculation |

**Edge Cases:**
- If `avg_volume_20d == 0` → skip signal (insufficient data)
- If volume data is not available for today → signal not evaluated
- Exclude days with known stock splits (volume distortion)

---

### 2.3 Bulk Deal Signal

**Definition:** Institutional investor or large entity executed a bulk purchase on NSE within the lookback window.

**Formula:**
```
recent_bulk_deals = [
    deal for deal in bulk_deals
    if deal.symbol == symbol
    and deal.deal_type == "BUY"
    and deal.date >= today - bulk_deal_lookback_days (default: 5)
]

bulk_deal_triggered = len(recent_bulk_deals) > 0
total_bulk_quantity = sum(deal.quantity for deal in recent_bulk_deals)
```

**Strength Score:**
```
if not bulk_deal_triggered: strength = 0.0
else:
    # Base score from recency
    most_recent_deal = min(recent_bulk_deals, key=lambda d: (today - d.date).days)
    days_ago = (today - most_recent_deal.date).days
    recency_score = 1.0 - (days_ago / bulk_deal_lookback_days) * 0.5
    
    # Bonus for multiple institutional buyers
    multi_buyer_bonus = 0.1 * min(len(set(d.client_name for d in recent_bulk_deals)) - 1, 3)
    
    strength = min(recency_score + multi_buyer_bonus, 1.0)
```

**Tunable Parameters:**

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `bulk_deal_lookback_days` | 5 | 3–10 | More days = more signals but less fresh |

---

## 3. Composite Signal Score

**Purpose:** Aggregate all triggered signals into a single score for ranking and confidence calculation.

**Formula:**
```python
SIGNAL_WEIGHTS = {
    "breakout": 0.35,
    "volume_spike": 0.35,
    "bulk_deal": 0.30
}

def compute_composite_score(signals: dict) -> float:
    weighted_sum = 0.0
    active_weight_sum = 0.0
    
    for signal_name, weight in SIGNAL_WEIGHTS.items():
        signal = signals.get(signal_name)
        if signal and signal.triggered:
            weighted_sum += signal.strength * weight
            active_weight_sum += weight
    
    if active_weight_sum == 0:
        return 0.0
    
    # Normalize by active weight (not total weight)
    # This prevents 1-signal stocks from being unfairly penalized
    base_score = weighted_sum / active_weight_sum
    
    # Multiplier for having multiple signals
    # 1 signal: 0.7x, 2 signals: 0.85x, 3 signals: 1.0x
    signal_count = sum(1 for s in signals.values() if s and s.triggered)
    count_multiplier = {1: 0.70, 2: 0.85, 3: 1.00}.get(signal_count, 0.70)
    
    return round(base_score * count_multiplier, 4)
```

**Score Interpretation:**

| Score Range | Interpretation |
|-------------|---------------|
| 0.0 – 0.40 | Weak — not worth showing |
| 0.41 – 0.60 | Moderate — WATCH territory |
| 0.61 – 0.75 | Strong — potential BUY |
| 0.76 – 1.00 | Very strong — high-confidence BUY |

---

## 4. Backtesting Engine

### 4.1 Signal Pattern Matching

**Purpose:** Find historical occurrences of the same signal pattern to measure past performance.

**Algorithm:**
```python
def find_historical_matches(
    symbol: str,
    signal_types: list[str],     # e.g., ["breakout", "volume_spike"]
    historical_data: pd.DataFrame,
    lookback_years: int = 2,
    max_matches: int = 5
) -> list[dict]:
    
    matches = []
    data = historical_data.sort_index()   # chronological
    
    for i in range(30, len(data) - 5):    # need 30 days history + 5 days future
        date = data.index[i]
        
        # Check each required signal type
        signal_match = True
        
        if "breakout" in signal_types:
            resistance = data["Close"][i-30:i].max()
            if not (data["Close"][i] > resistance):
                signal_match = False
        
        if "volume_spike" in signal_types:
            avg_vol = data["Volume"][i-20:i].mean()
            if not (data["Volume"][i] >= 2.0 * avg_vol):
                signal_match = False
        
        if signal_match:
            # Measure return at T+5 trading days
            future_price = data["Close"][i + 5]
            entry_price = data["Close"][i]
            return_pct = (future_price - entry_price) / entry_price * 100
            
            matches.append({
                "date": date.strftime("%Y-%m-%d"),
                "entry_price": float(entry_price),
                "exit_price": float(future_price),
                "return_pct": round(float(return_pct), 2),
                "profitable": return_pct > 0
            })
    
    # Return the most recent N matches
    return matches[-max_matches:]
```

---

### 4.2 Backtest Statistics

```python
def compute_backtest_stats(matches: list[dict]) -> dict:
    if not matches:
        return {"matches": 0, "success_rate": None, ...}
    
    returns = [m["return_pct"] for m in matches]
    profitable = [m for m in matches if m["profitable"]]
    
    return {
        "matches": len(matches),
        "success_rate": round(len(profitable) / len(matches) * 100, 1),
        "avg_return_pct": round(sum(returns) / len(returns), 2),
        "median_return_pct": round(sorted(returns)[len(returns) // 2], 2),
        "best_case_pct": round(max(returns), 2),
        "worst_case_pct": round(min(returns), 2),
        "cases": matches
    }
```

---

### 4.3 Backtest Quality Score

Used in confidence calculation to weight backtest evidence.

```python
def backtest_quality_score(stats: dict) -> float:
    if stats["matches"] == 0:
        return 0.0
    
    # Base: success rate (0 to 1)
    base = stats["success_rate"] / 100
    
    # Sample size confidence factor (more matches = more trustworthy)
    # 5 matches = full confidence, fewer = discounted
    sample_factor = min(stats["matches"] / 5.0, 1.0)
    
    # Penalize if best case is very high but avg is low (inconsistent)
    consistency_factor = 1.0
    if stats["avg_return_pct"] > 0 and stats["best_case_pct"] > 0:
        consistency_ratio = stats["avg_return_pct"] / stats["best_case_pct"]
        consistency_factor = min(0.5 + consistency_ratio * 0.5, 1.0)
    
    return round(base * sample_factor * consistency_factor, 4)
```

---

## 5. Confidence Score Calculation

**Purpose:** Produce a single 0–100 score representing the overall quality of the opportunity.

**Formula:**
```python
CONFIDENCE_WEIGHTS = {
    "composite_signal": 0.40,   # Signal strength (breakout / volume / bulk deal)
    "backtest_quality": 0.40,   # Historical validation
    "signal_count":     0.20    # Reward for multiple confirming signals
}

def compute_confidence(
    composite_score: float,     # 0.0 – 1.0
    backtest_quality: float,    # 0.0 – 1.0
    signal_count: int           # 1, 2, or 3
) -> float:
    
    # Signal count component: 1 signal = 0.33, 2 = 0.67, 3 = 1.0
    signal_count_score = min(signal_count / 3, 1.0)
    
    raw_confidence = (
        composite_score    * CONFIDENCE_WEIGHTS["composite_signal"] +
        backtest_quality   * CONFIDENCE_WEIGHTS["backtest_quality"] +
        signal_count_score * CONFIDENCE_WEIGHTS["signal_count"]
    )
    
    # Scale to 0–100 and round to 1 decimal
    return round(raw_confidence * 100, 1)
```

**Action Mapping:**

| Confidence | Action | Color |
|------------|--------|-------|
| ≥ 70 | BUY | Green |
| 50 – 69 | WATCH | Yellow |
| < 50 | AVOID | Red |

---

## 6. Trade Parameter Calculation

**Purpose:** Generate specific entry, target, and stop-loss prices for BUY decisions.

```python
def compute_trade_parameters(
    current_price: float,
    resistance_level: float,
    backtest_avg_return: float,   # percentage, e.g., 5.2
    support_level: float = None
) -> dict:
    
    # Entry: current market price (buy at market)
    entry = current_price
    
    # Target: entry + avg historical return (minimum 3%)
    target_return = max(backtest_avg_return, 3.0) / 100
    target = round(entry * (1 + target_return), 2)
    
    # Stop-loss: 3% below breakout resistance level
    # This invalidates the breakout if price falls back through resistance
    if resistance_level:
        stop_loss = round(resistance_level * 0.97, 2)
    elif support_level:
        stop_loss = round(support_level * 0.99, 2)
    else:
        stop_loss = round(entry * 0.93, 2)   # default 7% stop
    
    # Risk:Reward ratio
    reward = target - entry
    risk = entry - stop_loss
    rr_ratio = round(reward / risk, 2) if risk > 0 else 0.0
    
    return {
        "entry_price": round(entry, 2),
        "target_price": target,
        "stop_loss": stop_loss,
        "rr_ratio": rr_ratio,
        "reward_pct": round(reward / entry * 100, 2),
        "risk_pct": round(risk / entry * 100, 2)
    }
```

**Quality Gate:** If `rr_ratio < 1.0`, action is downgraded to WATCH (not favorable risk profile).

---

## 7. Outcome Measurement (T+5)

**Purpose:** Measure actual outcome of past BUY recommendations at 5 trading days after signal.

```python
def measure_outcome(
    decision: Decision,
    price_at_t5: float
) -> dict:
    
    entry = decision.entry_price
    return_pct = (price_at_t5 - entry) / entry * 100
    
    # Classify outcome
    if return_pct > 1.0:
        result = "profit"
    elif return_pct < -1.0:
        result = "loss"
    else:
        result = "neutral"
    
    return {
        "exit_price": price_at_t5,
        "return_pct": round(return_pct, 2),
        "result": result,
        "measured_at": datetime.utcnow()
    }
```

---

## 8. LLM Prompt Engineering

### 8.1 Reasoning Prompt

```python
REASONING_PROMPT = """You are a professional stock market analyst writing a brief opportunity report.

Given the following signal data for {symbol}, write a 3-5 sentence explanation of why this is an opportunity.

STRICT RULES:
1. Every sentence MUST reference a specific number or data point from the signal data below
2. Do NOT use vague phrases like "looks bullish" or "showing strength" without supporting data
3. If a signal is not triggered, do NOT mention it
4. Write in clear, simple English (not jargon-heavy)
5. Final sentence should reference the backtest success rate

Signal Data:
{signal_json}

Write only the explanation paragraph. No bullet points. No headers.
"""

def build_reasoning_prompt(symbol: str, signals: dict, backtest: dict) -> str:
    signal_data = {
        "symbol": symbol,
        "price": signals["price"],
        "signals": {k: v for k, v in signals.items() if v.get("triggered")},
        "backtest": {
            "matches": backtest["matches"],
            "success_rate": backtest["success_rate"],
            "avg_return_pct": backtest["avg_return_pct"]
        }
    }
    return REASONING_PROMPT.format(
        symbol=symbol,
        signal_json=json.dumps(signal_data, indent=2)
    )
```

### 8.2 Post-Processing Validation

```python
def validate_reasoning(text: str, signal_data: dict) -> bool:
    """
    Check that the reasoning actually references data values.
    Returns False if reasoning is too generic.
    """
    # Check that at least 2 numeric values from signal data appear in text
    numbers_in_data = [
        str(signal_data["price"]),
        str(signal_data.get("volume_ratio", "")),
        str(signal_data.get("backtest", {}).get("success_rate", ""))
    ]
    
    matches = sum(1 for num in numbers_in_data if num in text and num != "")
    return matches >= 2
```

---

## 9. Computation Performance Targets

| Computation | Max Duration |
|-------------|-------------|
| Breakout detection (single stock) | < 10ms |
| Volume spike detection (single stock) | < 5ms |
| Bulk deal lookup (single stock) | < 20ms |
| Composite score calculation | < 1ms |
| Backtesting (single stock, 2yr data) | < 500ms |
| Decision calculation | < 5ms |
| LLM reasoning generation | < 5 seconds |
| Full pipeline per stock | < 6 seconds |
| Full scan (100 stocks, parallel) | < 60 seconds |

---

## 10. Parameter Tuning Log

Document all parameter changes for reproducibility.

| Date | Parameter | Old Value | New Value | Reason |
|------|-----------|-----------|-----------|--------|
| 2026-03-25 | `breakout_lookback_days` | 20 | 30 | 20-day resistance too weak in backtests |
| 2026-03-25 | `volume_spike_threshold` | 1.5 | 2.0 | Too many false positives at 1.5x |
| 2026-03-25 | `bulk_deal_lookback_days` | 3 | 5 | Missed deals on T-4 in validation set |

---

*Last updated: 2026-03-25 | Version: 1.0*
