"""Unit tests for SignalAgent external (7-signal) mode.

Tests:
  test_signal_agent_active_mode_uses_grouped_scoring
    Verifies that mode="active" with full external_context produces a grouped
    composite score and activates news_sentiment + social_sentiment signals.

  test_signal_agent_active_mode_falls_back_without_external_data
    Verifies that mode="active" with no external_context falls back to
    legacy_fallback mode (3 signals, legacy composite score).
"""
from agents.signal_agent import SignalAgent


def _build_market_data():
    ohlcv = []
    for i in range(35):
        ohlcv.append(
            {
                "date": f"2026-03-{i+1:02d}",
                "open": 100.0,
                "high": 102.0,
                "low": 99.0,
                "close": 100.0,
                "volume": 10000,
            }
        )
    return {
        "symbol": "INFY",
        "current_price": 111.0,
        "volume_today": 45000,
        "ohlcv_short": ohlcv,
    }


def test_signal_agent_active_mode_uses_grouped_scoring():
    agent = SignalAgent()
    market_data = _build_market_data()
    bulk_deals = [
        {
            "date": "2026-03-27",
            "deal_type": "BUY",
            "client_name": "AXIS MF",
            "price": 109.5,
            "quantity": 500000,
        }
    ]
    external_context = {
        "news_sentiment": {"available": True, "article_count": 3, "weighted_sentiment": 0.45, "avg_confidence": 0.8},
        "social_sentiment": {"available": True, "sample_count": 10, "mention_zscore": 2.5, "positive_ratio": 0.72},
        "insider_filing": {"available": True, "filing_count": 1, "positive_filing_score": 0.7},
        "macro_indicator": {"available": True, "sample_count": 1, "sector_macro_score": 0.4, "freshness_minutes": 20},
    }

    result = agent.detect_signals(market_data, bulk_deals, external_context=external_context, mode="active")
    assert result["signal_diagnostics"]["mode_effective"] == "active"
    assert result["grouped_composite_score"] is not None
    assert result["composite_score"] == result["grouped_composite_score"]
    assert result["max_signal_count"] == 7
    assert result["extra_signals"]["news_sentiment"]["triggered"] is True
    assert result["extra_signals"]["social_sentiment"]["triggered"] is True


def test_signal_agent_active_mode_falls_back_without_external_data():
    agent = SignalAgent()
    market_data = _build_market_data()
    bulk_deals = []

    result = agent.detect_signals(market_data, bulk_deals, external_context=None, mode="active")
    assert result["signal_diagnostics"]["mode_effective"] == "legacy_fallback"
    assert result["composite_score"] == result["legacy_composite_score"]
    assert result["max_signal_count"] == 3
