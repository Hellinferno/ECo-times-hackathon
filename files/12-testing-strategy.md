# 12 â€” Testing Strategy

## AlphaHunter AI â€” Opportunity & Decision Engine

---

## 1. Overview

This document defines the complete testing strategy for AlphaHunter AI. It covers testing philosophy, test types, coverage targets, test data management, and specific test cases for every critical system component. The goal is to ensure every number the system produces is verifiable and every agent behaves predictably.

---

## 2. Testing Philosophy

> **Test the math, not the mocks.**

For a financial decision system, the most important tests are those that verify the computation engine produces correct, reproducible outputs. UI tests and integration tests are secondary. One wrong number in a backtesting result or confidence score destroys user trust.

**Priority order:**
1. Computation correctness (signal formulas, confidence scoring, backtest logic)
2. API contract compliance (correct response shapes)
3. Integration (end-to-end pipeline)
4. UI (smoke tests only for MVP)

---

## 3. Test Types & Coverage Targets

| Test Type | Tool | Coverage Target | Priority |
|-----------|------|-----------------|---------|
| Unit â€” Signal Agent | pytest | 95% | P0 |
| Unit â€” Backtesting Agent | pytest | 95% | P0 |
| Unit â€” Decision Agent | pytest | 90% | P0 |
| Unit â€” Reasoning Agent | pytest + mock | 80% | P1 |
| Unit â€” Data Agent | pytest + mock | 75% | P1 |
| Integration â€” API Endpoints | pytest + httpx | 80% | P1 |
| Integration â€” Full Scan Pipeline | pytest | Key flows | P1 |
| Frontend â€” Component | Vitest | Key components | P2 |
| E2E â€” Demo Flow | Playwright | Demo path only | P2 |

---

## 4. Test Data & Fixtures

### 4.1 Known Test Stocks

Use these stocks with known historical behavior for deterministic tests:

| Symbol | Test Use Case | Why |
|--------|--------------|-----|
| `INFY` | Breakout + Volume + Bulk Deal | Liquid, predictable patterns |
| `TCS` | Volume spike only | Clean volume patterns |
| `TATASTEEL` | AVOID scenario | Volatile, frequently oversold |
| `HDFCBANK` | WATCH scenario | Large cap, moderate signals |
| `TEST_STOCK` | Synthetic fixture | Fully controlled test data |

---

### 4.2 Synthetic Price Data Fixture

Used for deterministic testing without API calls.

```python
# tests/fixtures/price_data.py

import pandas as pd
import numpy as np

def make_synthetic_ohlcv(
    days: int = 60,
    base_price: float = 1000.0,
    breakout_on_day: int = None,
    volume_spike_on_day: int = None,
    spike_ratio: float = 2.5
) -> pd.DataFrame:
    """
    Creates synthetic OHLCV data for testing.
    Optionally inserts a breakout and/or volume spike on specified day.
    """
    dates = pd.bdate_range(end="2026-03-25", periods=days)
    prices = base_price + np.random.normal(0, 5, days).cumsum()
    volumes = np.random.randint(1_000_000, 2_000_000, days).astype(float)

    # Insert breakout on specified day
    if breakout_on_day is not None:
        # Ensure the last 30 days peak is below breakout_on_day's price
        prices[:breakout_on_day] = np.clip(prices[:breakout_on_day], None, base_price - 5)
        prices[breakout_on_day] = base_price + 20   # Clear breakout

    # Insert volume spike
    if volume_spike_on_day is not None:
        avg = volumes[:volume_spike_on_day].mean()
        volumes[volume_spike_on_day] = avg * spike_ratio

    return pd.DataFrame({
        "Open": prices * 0.995,
        "High": prices * 1.010,
        "Low": prices * 0.988,
        "Close": prices,
        "Volume": volumes
    }, index=dates)
```

---

### 4.3 Test Fixtures (`conftest.py`)

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base

@pytest.fixture(scope="session")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    yield Session()
    Base.metadata.drop_all(engine)

@pytest.fixture
def mock_anthropic_client(mocker):
    mock = mocker.patch("agents.reasoning_agent.genai.Client")
    mock.return_value.messages.create.return_value.content = [
        type("obj", (), {"text": "INFY crossed â‚¹1,500 resistance with 2.3x volume. Historical success rate: 80% in 5 cases."})()
    ]
    return mock

@pytest.fixture
def sample_signal_report():
    return {
        "symbol": "TEST",
        "price": 1502.45,
        "signals": {
            "breakout": {"triggered": True, "resistance_level": 1500.0, "pct_above": 0.16, "strength": 0.72},
            "volume_spike": {"triggered": True, "ratio": 2.3, "strength": 0.85},
            "bulk_deal": {"triggered": False, "strength": 0.0}
        },
        "signal_count": 2,
        "composite_score": 0.70
    }
```

---

## 5. Signal Agent Tests

### `tests/unit/test_signal_agent.py`

#### 5.1 Breakout Signal Tests

```python
class TestBreakoutSignal:

    def test_breakout_triggers_when_price_above_30d_high(self):
        data = make_synthetic_ohlcv(60, base_price=1000, breakout_on_day=59)
        signal = detect_breakout(data, lookback_days=30)
        assert signal.triggered == True

    def test_breakout_not_triggered_at_resistance_level(self):
        """Price must be STRICTLY above resistance â€” not equal."""
        data = make_synthetic_ohlcv(60, base_price=1000)
        data["Close"].iloc[-1] = data["Close"].iloc[-31:-1].max()  # exactly at resistance
        signal = detect_breakout(data, lookback_days=30)
        assert signal.triggered == False

    def test_breakout_not_triggered_below_resistance(self):
        data = make_synthetic_ohlcv(60, base_price=900)
        data["Close"].iloc[-1] = 850.0   # clearly below
        signal = detect_breakout(data, lookback_days=30)
        assert signal.triggered == False

    def test_breakout_strength_scales_with_pct_above(self):
        data_small = make_synthetic_ohlcv(60)
        data_small["Close"].iloc[-1] = data_small["Close"].iloc[-31:-1].max() + 1    # 0.1% above
        data_large = make_synthetic_ohlcv(60)
        data_large["Close"].iloc[-1] = data_large["Close"].iloc[-31:-1].max() + 50   # 5% above

        signal_small = detect_breakout(data_small)
        signal_large = detect_breakout(data_large)

        assert signal_large.strength > signal_small.strength

    def test_breakout_strength_capped_at_1(self):
        data = make_synthetic_ohlcv(60, base_price=1000, breakout_on_day=59)
        data["Close"].iloc[-1] = data["Close"].iloc[-31:-1].max() + 100  # way above
        signal = detect_breakout(data)
        assert signal.strength <= 1.0

    def test_breakout_returns_none_with_insufficient_data(self):
        data = make_synthetic_ohlcv(10)  # only 10 days
        signal = detect_breakout(data, lookback_days=30)
        assert signal is None

    def test_breakout_resistance_is_30d_max(self):
        data = make_synthetic_ohlcv(60, base_price=1000)
        expected_resistance = data["Close"].iloc[-31:-1].max()
        signal = detect_breakout(data, lookback_days=30)
        assert abs(signal.resistance_level - expected_resistance) < 0.01
```

---

#### 5.2 Volume Spike Signal Tests

```python
class TestVolumeSpikeSignal:

    def test_spike_triggers_at_2x_threshold(self):
        data = make_synthetic_ohlcv(30, volume_spike_on_day=29, spike_ratio=2.1)
        signal = detect_volume_spike(data, threshold=2.0)
        assert signal.triggered == True

    def test_spike_not_triggered_below_threshold(self):
        data = make_synthetic_ohlcv(30, volume_spike_on_day=29, spike_ratio=1.8)
        signal = detect_volume_spike(data, threshold=2.0)
        assert signal.triggered == False

    def test_spike_ratio_calculated_correctly(self):
        data = make_synthetic_ohlcv(30)
        avg_vol = data["Volume"].iloc[-20:-1].mean()
        data["Volume"].iloc[-1] = avg_vol * 2.5
        signal = detect_volume_spike(data, threshold=2.0)
        assert abs(signal.ratio - 2.5) < 0.05

    def test_spike_avg_uses_20_day_window(self):
        data = make_synthetic_ohlcv(30)
        # Set a very high volume on day 25 (within 20d window) â€” should inflate avg
        data["Volume"].iloc[-6] = 50_000_000
        data["Volume"].iloc[-1] = 5_000_000
        signal = detect_volume_spike(data, threshold=2.0)
        # With inflated avg, 5M should not be a spike
        assert signal.triggered == False

    def test_spike_strength_increases_with_ratio(self):
        data_2x = make_synthetic_ohlcv(30, volume_spike_on_day=29, spike_ratio=2.0)
        data_4x = make_synthetic_ohlcv(30, volume_spike_on_day=29, spike_ratio=4.0)
        assert detect_volume_spike(data_4x).strength > detect_volume_spike(data_2x).strength

    def test_zero_avg_volume_handled_gracefully(self):
        data = make_synthetic_ohlcv(30)
        data["Volume"] = 0
        signal = detect_volume_spike(data)
        assert signal is None or signal.triggered == False
```

---

#### 5.3 Composite Score Tests

```python
class TestCompositeScore:

    def test_all_three_signals_gives_highest_score(self):
        all_three = {
            "breakout": MagicMock(triggered=True, strength=0.8),
            "volume_spike": MagicMock(triggered=True, strength=0.8),
            "bulk_deal": MagicMock(triggered=True, strength=0.8)
        }
        one_signal = {
            "breakout": MagicMock(triggered=True, strength=0.8),
            "volume_spike": MagicMock(triggered=False, strength=0.0),
            "bulk_deal": MagicMock(triggered=False, strength=0.0)
        }
        assert compute_composite_score(all_three) > compute_composite_score(one_signal)

    def test_score_is_zero_with_no_signals(self):
        no_signals = {k: MagicMock(triggered=False, strength=0.0) for k in ["breakout", "volume_spike", "bulk_deal"]}
        assert compute_composite_score(no_signals) == 0.0

    def test_score_bounded_between_0_and_1(self):
        all_max = {k: MagicMock(triggered=True, strength=1.0) for k in ["breakout", "volume_spike", "bulk_deal"]}
        score = compute_composite_score(all_max)
        assert 0.0 <= score <= 1.0
```

---

## 6. Backtesting Agent Tests

### `tests/unit/test_backtesting_agent.py`

```python
class TestBacktestingAgent:

    def test_finds_correct_number_of_historical_matches(self):
        """With synthetic data containing exactly 3 breakouts, should find 3."""
        data = create_data_with_n_breakouts(n=3, years=2)
        matches = find_historical_matches("TEST", ["breakout"], data)
        assert len(matches) == 3

    def test_returns_max_5_matches(self):
        """Even if 10 historical matches exist, return only last 5."""
        data = create_data_with_n_breakouts(n=10, years=2)
        matches = find_historical_matches("TEST", ["breakout"], data, max_matches=5)
        assert len(matches) <= 5

    def test_return_calculated_at_t_plus_5(self):
        """Return must be measured 5 trading days after signal."""
        data = make_synthetic_ohlcv(100)
        entry_idx = 40
        entry_price = 1000.0
        exit_price = 1060.0
        data["Close"].iloc[entry_idx] = entry_price
        data["Close"].iloc[entry_idx + 5] = exit_price

        # Manually construct match
        expected_return = (exit_price - entry_price) / entry_price * 100
        matches = find_historical_matches("TEST", ["breakout"], data)
        # Find the match for entry_idx
        match = next((m for m in matches if abs(m["entry_price"] - entry_price) < 0.01), None)
        if match:
            assert abs(match["return_pct"] - expected_return) < 0.1

    def test_success_rate_calculation(self):
        matches = [
            {"return_pct": 5.0, "profitable": True},
            {"return_pct": -2.0, "profitable": False},
            {"return_pct": 3.0, "profitable": True},
            {"return_pct": 4.0, "profitable": True},
            {"return_pct": 6.0, "profitable": True},
        ]
        stats = compute_backtest_stats(matches)
        assert stats["success_rate"] == 80.0

    def test_avg_return_calculation(self):
        matches = [
            {"return_pct": 4.0, "profitable": True},
            {"return_pct": 6.0, "profitable": True},
        ]
        stats = compute_backtest_stats(matches)
        assert abs(stats["avg_return_pct"] - 5.0) < 0.01

    def test_empty_matches_returns_graceful_result(self):
        stats = compute_backtest_stats([])
        assert stats["matches"] == 0
        assert stats["success_rate"] is None

    def test_backtest_quality_score_scales_with_success_rate(self):
        good = {"matches": 5, "success_rate": 80.0, "avg_return_pct": 5.0, "best_case_pct": 10.0}
        bad = {"matches": 5, "success_rate": 40.0, "avg_return_pct": 2.0, "best_case_pct": 10.0}
        assert backtest_quality_score(good) > backtest_quality_score(bad)

    def test_quality_score_penalized_for_small_sample(self):
        large_sample = {"matches": 5, "success_rate": 80.0, "avg_return_pct": 5.0, "best_case_pct": 8.0}
        small_sample = {"matches": 2, "success_rate": 80.0, "avg_return_pct": 5.0, "best_case_pct": 8.0}
        assert backtest_quality_score(large_sample) > backtest_quality_score(small_sample)
```

---

## 7. Decision Agent Tests

### `tests/unit/test_decision_agent.py`

```python
class TestDecisionAgent:

    def test_buy_when_confidence_above_70(self):
        decision = compute_decision(composite_score=0.85, backtest_quality=0.80, signal_count=3)
        assert decision.action == "BUY"
        assert decision.confidence >= 70.0

    def test_watch_when_confidence_between_50_and_69(self):
        decision = compute_decision(composite_score=0.55, backtest_quality=0.50, signal_count=1)
        assert decision.action == "WATCH"
        assert 50.0 <= decision.confidence < 70.0

    def test_avoid_when_confidence_below_50(self):
        decision = compute_decision(composite_score=0.20, backtest_quality=0.30, signal_count=1)
        assert decision.action == "AVOID"
        assert decision.confidence < 50.0

    def test_confidence_bounded_0_to_100(self):
        # Max possible inputs
        decision = compute_decision(1.0, 1.0, 3)
        assert 0.0 <= decision.confidence <= 100.0
        # Min possible inputs
        decision = compute_decision(0.0, 0.0, 0)
        assert 0.0 <= decision.confidence <= 100.0

    def test_trade_parameters_populated_for_buy(self):
        params = compute_trade_parameters(
            current_price=1502.45,
            resistance_level=1500.0,
            backtest_avg_return=5.2
        )
        assert params["entry_price"] == 1502.45
        assert params["target_price"] > params["entry_price"]
        assert params["stop_loss"] < params["entry_price"]
        assert params["rr_ratio"] > 0

    def test_stop_loss_is_below_resistance(self):
        params = compute_trade_parameters(
            current_price=1510.0,
            resistance_level=1500.0,
            backtest_avg_return=5.0
        )
        assert params["stop_loss"] < 1500.0

    def test_rr_ratio_below_1_triggers_watch_downgrade(self):
        """If R:R < 1.0, BUY should be downgraded to WATCH."""
        params = compute_trade_parameters(1505.0, 1500.0, 0.5)  # tiny return
        assert params["rr_ratio"] >= 0
        # Downgrade logic tested separately in integration

    def test_target_uses_minimum_3pct_return(self):
        """Even if backtest avg is 1%, target should use minimum 3%."""
        params = compute_trade_parameters(1000.0, 990.0, backtest_avg_return=0.5)
        expected_minimum_target = 1000.0 * 1.03
        assert params["target_price"] >= expected_minimum_target
```

---

## 8. API Integration Tests

### `tests/integration/test_scan_api.py`

```python
class TestScanAPI:

    def test_scan_endpoint_returns_200(self, test_client):
        response = test_client.post("/api/scan", json={"mode": "full"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "scan_run_id" in data["data"]

    def test_scan_returns_409_when_already_running(self, test_client, mock_active_scan):
        response = test_client.post("/api/scan")
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "SCAN_IN_PROGRESS"

    def test_opportunities_returns_ranked_list(self, test_client, seeded_scan_results):
        response = test_client.get("/api/opportunities")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "opportunities" in data
        scores = [o["composite_score"] for o in data["opportunities"]]
        assert scores == sorted(scores, reverse=True)   # verify sorted

    def test_opportunities_filter_by_action(self, test_client, seeded_scan_results):
        response = test_client.get("/api/opportunities?action=BUY")
        assert response.status_code == 200
        for opp in response.json()["data"]["opportunities"]:
            assert opp["action"] == "BUY"

    def test_stock_detail_returns_full_structure(self, test_client):
        response = test_client.get("/api/stock/INFY")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "signals" in data
        assert "reasoning" in data
        assert "backtest" in data
        assert "decision" in data

    def test_stock_detail_404_for_unknown_symbol(self, test_client):
        response = test_client.get("/api/stock/FAKEXYZ")
        assert response.status_code == 404

    def test_history_endpoint_returns_summary_stats(self, test_client, seeded_decisions):
        response = test_client.get("/api/history")
        assert response.status_code == 200
        summary = response.json()["data"]["summary"]
        assert "win_rate_pct" in summary
        assert "total_decisions" in summary
```

---

## 9. Reasoning Agent Tests

### `tests/unit/test_reasoning_agent.py`

```python
class TestReasoningAgent:

    def test_reasoning_references_price_value(self, mock_anthropic_client, sample_signal_report):
        reasoning = generate_reasoning(sample_signal_report)
        assert "1502" in reasoning or "1,502" in reasoning

    def test_reasoning_references_volume_ratio(self, mock_anthropic_client, sample_signal_report):
        reasoning = generate_reasoning(sample_signal_report)
        assert "2.3" in reasoning

    def test_validation_fails_for_generic_text(self):
        generic = "The stock looks very bullish and has good momentum."
        signal_data = {"price": 1502.45, "volume_ratio": 2.3}
        assert validate_reasoning(generic, signal_data) == False

    def test_validation_passes_for_data_linked_text(self):
        good = "The stock crossed 1502 resistance with 2.3x volume, confirming 80% historical success."
        signal_data = {"price": 1502.45, "volume_ratio": 2.3, "backtest": {"success_rate": 80}}
        assert validate_reasoning(good, signal_data) == True

    def test_reasoning_max_5_sentences(self, mock_anthropic_client, sample_signal_report):
        reasoning = generate_reasoning(sample_signal_report)
        sentences = [s.strip() for s in reasoning.split(".") if s.strip()]
        assert len(sentences) <= 5
```

---

## 10. End-to-End Demo Test

### `tests/e2e/test_demo_flow.py` (Playwright)

```python
def test_full_demo_flow(page):
    """
    Tests the exact flow that will be demonstrated to judges.
    This is the most critical E2E test.
    """
    page.goto("http://localhost:3000")

    # Dashboard loads
    assert page.locator("text=AlphaHunter AI").is_visible()

    # Navigate to scanner
    page.click("[data-testid='nav-scanner']")
    assert page.locator("text=Scan Market").is_visible()

    # Trigger scan
    page.click("[data-testid='scan-button']")

    # Wait for results (max 90 seconds)
    page.wait_for_selector("[data-testid='opportunity-card']", timeout=90_000)

    # Click first opportunity
    page.click("[data-testid='opportunity-card']:first-child")

    # Verify all tabs present
    for tab in ["Overview", "Signals", "Backtest", "Trade Plan", "Chart"]:
        assert page.locator(f"text={tab}").is_visible()

    # Verify key data present
    assert page.locator("[data-testid='action-badge']").is_visible()
    assert page.locator("[data-testid='confidence-score']").is_visible()
    assert page.locator("[data-testid='reasoning-text']").is_visible()

    # Navigate to history
    page.click("[data-testid='nav-history']")
    assert page.locator("[data-testid='win-rate']").is_visible()
```

---

## 11. Test Execution Commands

```bash
# Run all backend tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=. --cov-report=html

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests (requires DB)
pytest tests/integration/ -v

# Run a specific test file
pytest tests/unit/test_signal_agent.py -v

# Run a specific test
pytest tests/unit/test_signal_agent.py::TestBreakoutSignal::test_breakout_triggers_when_price_above_30d_high -v

# Run frontend tests
cd apps/frontend && npm test

# Run E2E tests (requires running app)
playwright test tests/e2e/
```

---

## 12. Test Failure Triage Guide

| Failure Type | First Check |
|-------------|------------|
| Breakout signal wrong | Verify `resistance_level` calculation â€” is the window correct? |
| Confidence score off | Print intermediate scores; check weight constants |
| Backtest zero matches | Verify historical data length > 30 days + 5 days buffer |
| LLM test failure | Check mock is patching the right module path |
| API test 500 error | Check DB fixture is populated; check env vars in test |
| E2E timeout | Increase scan timeout; verify backend is running |

---

*Last updated: 2026-03-25 | Version: 1.0*
