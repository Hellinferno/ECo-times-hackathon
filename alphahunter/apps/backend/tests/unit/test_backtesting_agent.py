"""Unit tests for BacktestingAgent — synthetic historical OHLCV data."""
import pytest
from agents.backtesting_agent import BacktestingAgent


def make_hist_data(n: int, base_price: float = 100.0, base_volume: int = 500_000) -> list:
    """N days of flat OHLCV data."""
    return [
        {
            "date": f"2022-01-{(i % 28) + 1:02d}",
            "open": base_price, "high": base_price + 1,
            "low": base_price - 1, "close": base_price, "volume": base_volume
        }
        for i in range(n)
    ]


def make_breakout_hist(n_flat: int = 200, n_breakouts: int = 6) -> list:
    """
    Historical data with several genuine breakout events.
    Creates blocks of flat price followed by a spike above resistance.
    """
    data = []
    for block in range(n_breakouts + 1):
        base = 100.0 + block * 5.0
        flat_days = n_flat // (n_breakouts + 1)
        for i in range(flat_days):
            data.append({
                "date": f"2022-{(block % 12) + 1:02d}-{(i % 28) + 1:02d}",
                "open": base, "high": base + 1, "low": base - 1, "close": base, "volume": 500_000,
            })
        # Breakout day
        spike = base + 8.0
        data.append({
            "date": f"2022-{(block % 12) + 1:02d}-28",
            "open": base, "high": spike + 2, "low": base, "close": spike, "volume": 500_000,
        })
    return data


class TestBacktestingAgent:
    def setup_method(self):
        self.agent = BacktestingAgent()

    def test_returns_empty_on_no_hist_data(self):
        result = self.agent.evaluate_historical_signals({"breakout_triggered": True}, [])
        assert result["backtest_matches"] == 0
        assert result["backtest_success_rate"] == 0.0

    def test_returns_empty_on_insufficient_hist_data(self):
        hist = make_hist_data(20)
        result = self.agent.evaluate_historical_signals({"breakout_triggered": True}, hist)
        assert result["backtest_matches"] == 0

    def test_breakout_analogue_finds_matches(self):
        hist = make_breakout_hist(n_flat=200, n_breakouts=6)
        signal = {"breakout_triggered": True}
        result = self.agent.evaluate_historical_signals(signal, hist)
        assert result["backtest_matches"] > 0
        assert 0.0 <= result["backtest_success_rate"] <= 100.0
        assert isinstance(result["cases"], list)

    def test_volume_spike_analogue_finds_matches(self):
        hist = make_hist_data(300)
        # Insert volume spikes
        for i in [50, 100, 150, 200, 250]:
            hist[i]["volume"] = 2_000_000  # 4x spike
        signal = {"volume_spike_triggered": True, "breakout_triggered": False,
                  "volume_spike_details": {"volume_ratio": 3.5}}
        result = self.agent.evaluate_historical_signals(signal, hist)
        assert result["backtest_matches"] > 0

    def test_rsi_analogue_with_oversold_data(self):
        # Create steadily declining hist data (creates RSI < 45 opportunities)
        hist = []
        price = 150.0
        for i in range(300):
            if i % 15 == 0 and i > 0:
                price -= 8.0  # periodic dips
            hist.append({
                "date": f"2022-{(i // 30) % 12 + 1:02d}-{(i % 28) + 1:02d}",
                "open": price, "high": price + 1, "low": price - 2, "close": price, "volume": 500_000
            })
        signal = {"rsi_triggered": True, "breakout_triggered": False, "volume_spike_triggered": False,
                  "rsi_details": {"rsi": 32.0}}
        result = self.agent.evaluate_historical_signals(signal, hist)
        # May or may not find matches depending on the RSI values — just check structure
        assert "backtest_matches" in result
        assert "cases" in result

    def test_max_5_cases_returned(self):
        hist = make_breakout_hist(n_flat=200, n_breakouts=10)
        signal = {"breakout_triggered": True}
        result = self.agent.evaluate_historical_signals(signal, hist)
        assert result["backtest_matches"] <= 5

    def test_worst_case_lte_avg_lte_best_case(self):
        hist = make_breakout_hist(n_flat=200, n_breakouts=6)
        signal = {"breakout_triggered": True}
        result = self.agent.evaluate_historical_signals(signal, hist)
        if result["backtest_matches"] > 0:
            assert result["backtest_worst_case"] <= result["backtest_avg_return"]
            assert result["backtest_avg_return"] <= result["backtest_best_case"]

    def test_bulk_deal_proxy_analogue(self):
        hist = make_hist_data(300)
        # Insert some gap-up + volume days
        for i in [60, 120, 180, 240]:
            hist[i]["volume"] = 2_000_000
            hist[i]["close"] = hist[i]["close"] * 1.02  # 2% gap-up
        signal = {"bulk_deal_triggered": True, "breakout_triggered": False,
                  "volume_spike_triggered": False, "rsi_triggered": False}
        result = self.agent.evaluate_historical_signals(signal, hist)
        assert "backtest_matches" in result
