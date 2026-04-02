import json
import types as pytypes

import agents.reasoning_agent as reasoning_module
from agents.reasoning_agent import ReasoningAgent


def _signals():
    return {
        "breakout_triggered": True,
        "breakout_details": {
            "lookback_days": 30,
            "resistance_level": 1500.0,
            "pct_above": 2.3,
        },
        "volume_spike_triggered": True,
        "volume_spike_details": {
            "volume_ratio": 2.8,
            "avg_volume_20d": 1200000,
        },
        "bulk_deal_triggered": True,
        "bulk_deal_details": {
            "buyer": "Axis Mutual Fund",
            "quantity": 500000,
            "price": 1495.0,
            "latest_deal_date": "2026-03-25",
        },
    }


def _backtest():
    return {
        "backtest_matches": 6,
        "backtest_success_rate": 66.7,
        "backtest_avg_return": 4.2,
    }


def test_generate_explanation_uses_gemini_when_configured(monkeypatch):
    fake_response = json.dumps(
        {
            "llm_summary": (
                "INFY at 1525.0 broke 30-day resistance at 1500.0 and is 2.3% above it. "
                "Volume is 2.8x the 20-day average of 1200000, with Axis Mutual Fund buying 500000 shares at 1495.0. "
                "Backtests show 66.7% success and 4.2% average return."
            ),
            "key_factors": [
                "Breakout at 1500.0 with price at 1525.0",
                "Volume 2.8x versus 1200000 average",
                "Bulk deal 500000 shares at 1495.0",
            ],
            "risk_warnings": ["Backtest success is 66.7%, not guaranteed."],
        }
    )

    class FakeModels:
        def __init__(self):
            self.calls = []

        def generate_content(self, **kwargs):
            self.calls.append(kwargs)
            return pytypes.SimpleNamespace(text=fake_response)

    class FakeClient:
        def __init__(self, api_key):
            self.api_key = api_key
            self.models = FakeModels()

    monkeypatch.setattr(reasoning_module.settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(reasoning_module.settings, "GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.setattr(reasoning_module.settings, "LLM_MAX_TOKENS", 180)
    monkeypatch.setattr(reasoning_module, "genai", pytypes.SimpleNamespace(Client=FakeClient))
    monkeypatch.setattr(
        reasoning_module,
        "types",
        pytypes.SimpleNamespace(GenerateContentConfig=lambda **kwargs: kwargs),
    )

    agent = ReasoningAgent()
    result = agent.generate_explanation("INFY", 1525.0, _signals(), _backtest())

    assert isinstance(result, dict)
    assert result["llm_summary"].startswith("INFY at 1525.0 broke 30-day resistance")
    assert result["key_factors"][0] == "Breakout at 1500.0 with price at 1525.0"
    assert result["metadata"]["source"] == "llm"
    assert result["metadata"]["prompt_version"] == "reasoning-v2"
    assert result["metadata"]["validation_status"] == "passed"

    assert agent.client.api_key == "test-key"
    assert agent.client.models.calls[0]["model"] == "gemini-2.5-flash"
    assert "Stock: INFY" in agent.client.models.calls[0]["contents"]
    assert agent.client.models.calls[0]["config"]["max_output_tokens"] == 180


def test_generate_explanation_falls_back_when_genai_not_installed(monkeypatch):
    monkeypatch.setattr(reasoning_module.settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(reasoning_module, "genai", None)
    monkeypatch.setattr(reasoning_module, "types", None)

    agent = ReasoningAgent()
    result = agent.generate_explanation("INFY", 1525.0, _signals(), _backtest())

    assert isinstance(result, dict)
    assert "INFY presents a potential opportunity" in result["llm_summary"]
    assert "66.7%" in result["llm_summary"]
    assert result["metadata"]["source"] == "fallback"
    assert result["metadata"]["validation_status"] == "fallback"


def test_generate_explanation_falls_back_when_gemini_fails(monkeypatch):
    class FailingModels:
        def generate_content(self, **kwargs):
            raise RuntimeError("Gemini outage")

    class FakeClient:
        def __init__(self, api_key):
            self.models = FailingModels()

    monkeypatch.setattr(reasoning_module.settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(reasoning_module, "genai", pytypes.SimpleNamespace(Client=FakeClient))
    monkeypatch.setattr(
        reasoning_module,
        "types",
        pytypes.SimpleNamespace(GenerateContentConfig=lambda **kwargs: kwargs),
    )

    agent = ReasoningAgent()
    result = agent.generate_explanation("INFY", 1525.0, _signals(), _backtest())

    assert isinstance(result, dict)
    assert result["metadata"]["source"] == "fallback"
    assert "4.2%" in result["llm_summary"]


def test_invalid_llm_numeric_drift_falls_back(monkeypatch):
    fake_response = json.dumps(
        {
            "llm_summary": "INFY at 1600.0 broke resistance with strong momentum.",
            "key_factors": ["Breakout with strong conviction"],
            "risk_warnings": ["Momentum could fade."],
        }
    )

    class FakeModels:
        def generate_content(self, **kwargs):
            return pytypes.SimpleNamespace(text=fake_response)

    class FakeClient:
        def __init__(self, api_key):
            self.models = FakeModels()

    monkeypatch.setattr(reasoning_module.settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(reasoning_module, "genai", pytypes.SimpleNamespace(Client=FakeClient))
    monkeypatch.setattr(
        reasoning_module,
        "types",
        pytypes.SimpleNamespace(GenerateContentConfig=lambda **kwargs: kwargs),
    )

    agent = ReasoningAgent()
    result = agent.generate_explanation("INFY", 1525.0, _signals(), _backtest())

    assert result["metadata"]["source"] == "fallback"
    assert "1525.0" in result["llm_summary"]


def test_cache_key_differs_for_different_prices(monkeypatch):
    monkeypatch.setattr(reasoning_module.settings, "GEMINI_API_KEY", None)
    monkeypatch.setattr(reasoning_module, "genai", None)

    agent = ReasoningAgent()
    ctx1 = agent._build_prompt_context("INFY", 1525.0, _signals(), _backtest())
    ctx2 = agent._build_prompt_context("INFY", 1600.0, _signals(), _backtest())

    key1 = reasoning_module._make_cache_key(agent.model, ctx1)
    key2 = reasoning_module._make_cache_key(agent.model, ctx2)

    assert key1 != key2, "Different prices must produce different cache keys"
