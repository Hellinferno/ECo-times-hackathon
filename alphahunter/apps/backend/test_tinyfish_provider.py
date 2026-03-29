"""Unit tests for TinyFishProvider SSE parsing and error handling.

Tests:
  test_tinyfish_provider_parses_sse_payload
    Verifies that a valid SSE stream with a JSON events array is parsed into
    NormalizedSignalEvent objects with correct symbol, event_type, and Decimal fields.

  test_tinyfish_provider_handles_invalid_payload
    Verifies that non-JSON SSE lines and a non-JSON plain response both
    produce an empty event list (no exception raised).
"""
from decimal import Decimal

import requests

from providers.tinyfish_provider import TinyFishProvider
from providers.web_intel_provider import GoalSpec


class MockResponse:
    def __init__(self, lines=None, json_payload=None, status_code=200):
        self._lines = lines or []
        self._json_payload = json_payload or {}
        self.status_code = status_code

    def iter_lines(self):
        for line in self._lines:
            yield line

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._json_payload


def test_tinyfish_provider_parses_sse_payload(monkeypatch):
    response = MockResponse(
        lines=[
            b'data: {"events":[{"symbol":"INFY","sentiment":0.4,"confidence":0.9,"event_time":"2026-03-27T10:00:00Z"}]}',
            b"data: [DONE]",
        ]
    )

    def fake_post(*args, **kwargs):
        return response

    monkeypatch.setattr("providers.tinyfish_provider.requests.post", fake_post)
    provider = TinyFishProvider(api_key="test", endpoint="https://example.com")
    goals = [
        GoalSpec(
            source_type="news_sentiment",
            url="https://example.com",
            goal="Extract sentiment for INFY",
            symbol="INFY",
        )
    ]

    events = provider.run_goal_batch(goals=goals, timeout_secs=1, max_concurrency=1)
    assert len(events) == 1
    assert events[0].symbol == "INFY"
    assert events[0].event_type == "news_sentiment"
    assert isinstance(events[0].sentiment, Decimal)


def test_tinyfish_provider_handles_invalid_payload(monkeypatch):
    response = MockResponse(lines=[b"data: not-json", b"data: [DONE]"], json_payload={"result": "not-json"})

    def fake_post(*args, **kwargs):
        return response

    monkeypatch.setattr("providers.tinyfish_provider.requests.post", fake_post)
    provider = TinyFishProvider(api_key="test", endpoint="https://example.com")
    goals = [
        GoalSpec(
            source_type="social_sentiment",
            url="https://example.com",
            goal="Extract social sentiment",
            symbol="TCS",
        )
    ]

    events = provider.run_goal_batch(goals=goals, timeout_secs=1, max_concurrency=1)
    assert events == []
