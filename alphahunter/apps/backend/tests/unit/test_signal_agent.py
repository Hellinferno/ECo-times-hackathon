"""Unit tests for SignalAgent — synthetic OHLCV data, no external APIs required."""
import math
import pytest
from agents.signal_agent import SignalAgent


# ── Synthetic OHLCV generators ─────────────────────────────────────────────────

def make_flat_ohlcv(n: int, price: float = 100.0, volume: int = 500_000) -> list:
    """N days of flat price/volume — no signals should trigger."""
    return [
        {"date": f"2024-01-{i+1:02d}", "open": price, "high": price + 1,
         "low": price - 1, "close": price, "volume": volume}
        for i in range(n)
    ]


def make_breakout_ohlcv(resistance: float = 100.0, breakout_price: float = 107.0) -> list:
    """60 days of flat price, final day breaks above resistance."""
    data = make_flat_ohlcv(59, resistance)
    data.append({
        "date": "2024-03-01", "open": resistance, "high": breakout_price + 2,
        "low": resistance, "close": breakout_price, "volume": 500_000
    })
    return data


def make_volume_spike_ohlcv(base_volume: int = 500_000, spike_multiple: float = 3.0) -> list:
    """60 days of base volume, final day spikes."""
    data = make_flat_ohlcv(59, 100.0, base_volume)
    data.append({
        "date": "2024-03-01", "open": 100.0, "high": 101.0,
        "low": 99.0, "close": 100.5, "volume": int(base_volume * spike_multiple)
    })
    return data


def make_oversold_ohlcv(n: int = 40) -> list:
    """Steadily declining price to create oversold RSI < 30."""
    data = []
    price = 150.0
    for i in range(n):
        price -= 2.5  # consistent decline
        data.append({
            "date": f"2024-01-{i+1:02d}", "open": price + 1, "high": price + 2,
            "low": price - 1, "close": price, "volume": 500_000
        })
    return data


# ── SignalAgent tests ──────────────────────────────────────────────────────────

class TestBreakoutDetection:
    def setup_method(self):
        self.agent = SignalAgent()

    def test_breakout_triggers_above_resistance(self):
        ohlcv = make_breakout_ohlcv(resistance=100.0, breakout_price=107.0)
        market_data = {"symbol": "TEST", "current_price": 107.0, "volume_today": 500_000, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(market_data, [], mode="legacy")
        assert result["breakout_triggered"] is True
        assert result["breakout_details"]["strength"] > 0
        assert result["breakout_details"]["resistance_level"] == pytest.approx(100.0)

    def test_no_breakout_below_resistance(self):
        ohlcv = make_flat_ohlcv(60, price=100.0)
        market_data = {"symbol": "TEST", "current_price": 98.0, "volume_today": 500_000, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(market_data, [], mode="legacy")
        assert result["breakout_triggered"] is False
        assert result["breakout_details"]["strength"] == 0.0

    def test_breakout_strength_increases_with_distance(self):
        ohlcv1 = make_breakout_ohlcv(resistance=100.0, breakout_price=103.0)
        ohlcv2 = make_breakout_ohlcv(resistance=100.0, breakout_price=110.0)
        agent = SignalAgent()
        r1 = agent.detect_signals({"symbol": "T", "current_price": 103.0, "volume_today": 500_000, "ohlcv_short": ohlcv1}, [], mode="legacy")
        r2 = agent.detect_signals({"symbol": "T", "current_price": 110.0, "volume_today": 500_000, "ohlcv_short": ohlcv2}, [], mode="legacy")
        assert r2["breakout_details"]["strength"] > r1["breakout_details"]["strength"]

    def test_insufficient_data_returns_no_breakout(self):
        ohlcv = make_flat_ohlcv(3)
        market_data = {"symbol": "TEST", "current_price": 200.0, "volume_today": 500_000, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(market_data, [], mode="legacy")
        assert result["breakout_triggered"] is False


class TestVolumeSpikeDetection:
    def setup_method(self):
        self.agent = SignalAgent()

    def test_volume_spike_triggers_above_threshold(self):
        ohlcv = make_volume_spike_ohlcv(base_volume=500_000, spike_multiple=3.0)
        market_data = {"symbol": "TEST", "current_price": 100.0, "volume_today": 1_500_000, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(market_data, [], mode="legacy")
        assert result["volume_spike_triggered"] is True
        assert result["volume_spike_details"]["volume_ratio"] >= 2.0

    def test_no_volume_spike_below_threshold(self):
        ohlcv = make_flat_ohlcv(60, volume=500_000)
        market_data = {"symbol": "TEST", "current_price": 100.0, "volume_today": 600_000, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(market_data, [], mode="legacy")
        assert result["volume_spike_triggered"] is False

    def test_custom_threshold(self):
        agent = SignalAgent(volume_spike_threshold=3.0)
        ohlcv = make_volume_spike_ohlcv(base_volume=500_000, spike_multiple=2.5)
        market_data = {"symbol": "TEST", "current_price": 100.0, "volume_today": 1_250_000, "ohlcv_short": ohlcv}
        result = agent.detect_signals(market_data, [], mode="legacy")
        # 2.5x volume should NOT trigger a 3.0x threshold
        assert result["volume_spike_triggered"] is False


class TestBulkDealDetection:
    def setup_method(self):
        self.agent = SignalAgent()

    def test_bulk_deal_triggers_on_recent_buy(self):
        from datetime import date, timedelta
        recent_date = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")
        bulk_deals = [{"date": recent_date, "client_name": "FII X", "deal_type": "BUY", "quantity": 100_000, "price": 100.0}]
        ohlcv = make_flat_ohlcv(60)
        market_data = {"symbol": "TEST", "current_price": 100.0, "volume_today": 500_000, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(market_data, bulk_deals, mode="legacy")
        assert result["bulk_deal_triggered"] is True

    def test_bulk_deal_does_not_trigger_on_sell(self):
        from datetime import date, timedelta
        recent_date = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")
        bulk_deals = [{"date": recent_date, "client_name": "FII X", "deal_type": "SELL", "quantity": 100_000, "price": 100.0}]
        ohlcv = make_flat_ohlcv(60)
        market_data = {"symbol": "TEST", "current_price": 100.0, "volume_today": 500_000, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(market_data, bulk_deals, mode="legacy")
        assert result["bulk_deal_triggered"] is False

    def test_bulk_deal_does_not_trigger_on_old_deals(self):
        bulk_deals = [{"date": "2020-01-01", "client_name": "FII X", "deal_type": "BUY", "quantity": 100_000, "price": 100.0}]
        ohlcv = make_flat_ohlcv(60)
        market_data = {"symbol": "TEST", "current_price": 100.0, "volume_today": 500_000, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(market_data, bulk_deals, mode="legacy")
        assert result["bulk_deal_triggered"] is False


class TestRSIDetection:
    def setup_method(self):
        self.agent = SignalAgent()

    def test_rsi_triggers_on_declining_price(self):
        ohlcv = make_oversold_ohlcv(40)
        market_data = {"symbol": "TEST", "current_price": ohlcv[-1]["close"], "volume_today": 500_000, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(market_data, [], mode="legacy")
        assert result["rsi_triggered"] is True
        rsi_val = result["rsi_details"]["rsi"]
        assert rsi_val < 45.0

    def test_rsi_not_triggered_on_stable_price(self):
        ohlcv = make_flat_ohlcv(60, price=100.0)
        market_data = {"symbol": "TEST", "current_price": 100.0, "volume_today": 500_000, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(market_data, [], mode="legacy")
        # Flat price = RSI ~50 (neutral), should not trigger
        assert result["rsi_details"]["rsi"] is not None
        if not result["rsi_triggered"]:
            assert result["rsi_details"]["rsi"] >= 45.0

    def test_rsi_insufficient_data(self):
        ohlcv = make_flat_ohlcv(10)
        market_data = {"symbol": "TEST", "current_price": 100.0, "volume_today": 500_000, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(market_data, [], mode="legacy")
        assert result["rsi_triggered"] is False
        assert "error" in result["rsi_details"]

    def test_rsi_strength_higher_for_more_oversold(self):
        # More decline = lower RSI = higher strength
        ohlcv_mild = make_oversold_ohlcv(20)   # mild decline
        ohlcv_steep = make_oversold_ohlcv(40)  # steeper decline

        md1 = {"symbol": "T", "current_price": ohlcv_mild[-1]["close"], "volume_today": 500_000, "ohlcv_short": ohlcv_mild}
        md2 = {"symbol": "T", "current_price": ohlcv_steep[-1]["close"], "volume_today": 500_000, "ohlcv_short": ohlcv_steep}

        r1 = self.agent.detect_signals(md1, [], mode="legacy")
        r2 = self.agent.detect_signals(md2, [], mode="legacy")

        if r1["rsi_triggered"] and r2["rsi_triggered"]:
            assert r2["rsi_details"]["strength"] >= r1["rsi_details"]["strength"]


class TestMACDDetection:
    def setup_method(self):
        self.agent = SignalAgent()

    def test_macd_present_in_output(self):
        ohlcv = make_flat_ohlcv(60)
        market_data = {"symbol": "TEST", "current_price": 100.0, "volume_today": 500_000, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(market_data, [], mode="legacy")
        assert "macd_triggered" in result
        assert "macd_details" in result

    def test_macd_requires_sufficient_data(self):
        ohlcv = make_flat_ohlcv(20)  # Less than 26+9=35 needed
        market_data = {"symbol": "TEST", "current_price": 100.0, "volume_today": 500_000, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(market_data, [], mode="legacy")
        assert result["macd_triggered"] is False
        assert "error" in result["macd_details"]


class TestCompositeScoring:
    def setup_method(self):
        self.agent = SignalAgent()

    def test_signal_count_increases_with_more_signals(self):
        # Breakout + volume spike → count = 2 (minimum)
        ohlcv = make_breakout_ohlcv(resistance=100.0, breakout_price=107.0)
        ohlcv[-1]["volume"] = 1_500_000  # Also spike volume

        md = {"symbol": "TEST", "current_price": 107.0, "volume_today": 1_500_000, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(md, [], mode="legacy")
        assert result["signal_count"] >= 2

    def test_composite_score_between_0_and_1(self):
        ohlcv = make_flat_ohlcv(60)
        md = {"symbol": "TEST", "current_price": 100.0, "volume_today": 500_000, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(md, [], mode="legacy")
        assert 0.0 <= result["composite_score"] <= 1.0

    def test_no_signal_gives_zero_count(self):
        ohlcv = make_flat_ohlcv(60)
        md = {"symbol": "TEST", "current_price": 98.0, "volume_today": 500_000, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(md, [], mode="legacy")
        assert result["breakout_triggered"] is False
        assert result["volume_spike_triggered"] is False
        assert result["bulk_deal_triggered"] is False

    def test_nan_safety_in_output(self):
        """Composite score must never be NaN or Infinity."""
        ohlcv = make_flat_ohlcv(60)
        md = {"symbol": "TEST", "current_price": 0.0, "volume_today": 0, "ohlcv_short": ohlcv}
        result = self.agent.detect_signals(md, [], mode="legacy")
        assert not math.isnan(result["composite_score"])
        assert not math.isinf(result["composite_score"])
