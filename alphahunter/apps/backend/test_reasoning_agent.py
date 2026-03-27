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
    class FakeModels:
        def __init__(self):
            self.calls = []

        def generate_content(self, **kwargs):
            self.calls.append(kwargs)
            return pytypes.SimpleNamespace(text="Gemini-generated market explanation.")

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

    assert result == "Gemini-generated market explanation."
    assert agent.client.api_key == "test-key"
    assert agent.client.models.calls[0]["model"] == "gemini-2.5-flash"
    assert "Stock: INFY" in agent.client.models.calls[0]["contents"]
    assert agent.client.models.calls[0]["config"]["max_output_tokens"] == 180


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

    assert "INFY presents a potential opportunity" in result
    assert "Historically, this pattern succeeded 66.7%" in result
