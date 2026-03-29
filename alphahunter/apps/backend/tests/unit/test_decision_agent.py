"""Unit tests for DecisionAgent — confidence formula edge cases."""
import pytest
from agents.decision_agent import DecisionAgent


class TestDecisionAgent:
    def setup_method(self):
        self.agent = DecisionAgent()

    def test_high_confidence_gives_buy(self):
        bt = {"backtest_matches": 4, "backtest_success_rate": 80.0, "backtest_avg_return": 3.5}
        signal = {"signal_count": 3, "max_signal_count": 5, "composite_score": 0.8}
        result = self.agent.evaluate(100.0, 0.8, bt, signal)
        assert result["action"] == "BUY"
        assert result["confidence"] >= 70.0

    def test_low_signal_gives_avoid(self):
        bt = {"backtest_matches": 0, "backtest_success_rate": 0.0, "backtest_avg_return": 0.0}
        signal = {"signal_count": 0, "max_signal_count": 5, "composite_score": 0.0}
        result = self.agent.evaluate(100.0, 0.0, bt, signal)
        assert result["action"] == "AVOID"
        assert result["confidence"] < 50.0

    def test_no_backtest_matches_reduces_confidence(self):
        bt_with = {"backtest_matches": 5, "backtest_success_rate": 80.0, "backtest_avg_return": 3.0}
        bt_without = {"backtest_matches": 0, "backtest_success_rate": 0.0, "backtest_avg_return": 0.0}
        signal = {"signal_count": 3, "max_signal_count": 5, "composite_score": 0.8}

        result_with = self.agent.evaluate(100.0, 0.8, bt_with, signal)
        result_without = self.agent.evaluate(100.0, 0.8, bt_without, signal)

        assert result_with["confidence"] > result_without["confidence"]

    def test_trade_parameters_present_on_buy(self):
        bt = {"backtest_matches": 4, "backtest_success_rate": 75.0, "backtest_avg_return": 2.5}
        signal = {"signal_count": 3, "max_signal_count": 5, "composite_score": 0.8}
        result = self.agent.evaluate(150.0, 0.8, bt, signal)
        if result["action"] == "BUY":
            assert result["entry_price"] is not None
            assert result["target_price"] is not None
            assert result["stop_loss"] is not None
            assert result["target_price"] > result["entry_price"]
            assert result["stop_loss"] < result["entry_price"]

    def test_rr_ratio_positive_on_buy(self):
        bt = {"backtest_matches": 4, "backtest_success_rate": 80.0, "backtest_avg_return": 3.0}
        signal = {"signal_count": 3, "max_signal_count": 5, "composite_score": 0.8}
        result = self.agent.evaluate(100.0, 0.8, bt, signal)
        if result["action"] == "BUY" and result["rr_ratio"] is not None:
            assert float(result["rr_ratio"]) > 0

    def test_confidence_bounded_0_to_100(self):
        for composite in [0.0, 0.3, 0.5, 0.8, 1.0]:
            for matches in [0, 2, 5]:
                bt = {"backtest_matches": matches, "backtest_success_rate": 70.0, "backtest_avg_return": 2.0}
                signal = {"signal_count": 3, "max_signal_count": 5, "composite_score": composite}
                result = self.agent.evaluate(100.0, composite, bt, signal)
                assert 0.0 <= result["confidence"] <= 100.0, f"Confidence out of range: {result['confidence']}"
