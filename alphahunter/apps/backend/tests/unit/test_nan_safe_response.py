"""Unit tests for NaN/Infinity sanitisation — safety-critical for yfinance output."""
import json
import math
import pytest
from main import NanSafeJSONResponse, _sanitize_nan


class TestSanitizeNan:
    def test_nan_replaced_with_none(self):
        assert _sanitize_nan(float("nan")) is None

    def test_inf_replaced_with_none(self):
        assert _sanitize_nan(float("inf")) is None

    def test_neg_inf_replaced_with_none(self):
        assert _sanitize_nan(float("-inf")) is None

    def test_valid_float_unchanged(self):
        assert _sanitize_nan(3.14) == 3.14

    def test_zero_unchanged(self):
        assert _sanitize_nan(0.0) == 0.0

    def test_nested_dict(self):
        data = {"price": float("nan"), "volume": 1000, "ratio": float("inf")}
        result = _sanitize_nan(data)
        assert result["price"] is None
        assert result["volume"] == 1000
        assert result["ratio"] is None

    def test_nested_list(self):
        data = [1.0, float("nan"), 3.0, float("inf")]
        result = _sanitize_nan(data)
        assert result == [1.0, None, 3.0, None]

    def test_deeply_nested(self):
        data = {"ohlcv": [{"close": float("nan"), "volume": 500_000}]}
        result = _sanitize_nan(data)
        assert result["ohlcv"][0]["close"] is None
        assert result["ohlcv"][0]["volume"] == 500_000

    def test_none_input_unchanged(self):
        assert _sanitize_nan(None) is None

    def test_string_unchanged(self):
        assert _sanitize_nan("hello") == "hello"

    def test_int_unchanged(self):
        assert _sanitize_nan(42) == 42

    def test_bool_unchanged(self):
        assert _sanitize_nan(True) is True

    def test_empty_dict_unchanged(self):
        assert _sanitize_nan({}) == {}

    def test_empty_list_unchanged(self):
        assert _sanitize_nan([]) == []


class TestNanSafeJSONResponse:
    def test_renders_nan_as_null(self):
        response = NanSafeJSONResponse({"value": float("nan")})
        body = json.loads(response.body)
        assert body["value"] is None

    def test_renders_valid_data_correctly(self):
        data = {"symbol": "INFY", "price": 1500.5, "volume": 100_000}
        response = NanSafeJSONResponse(data)
        body = json.loads(response.body)
        assert body == data

    def test_renders_mixed_data(self):
        data = {"price": 100.0, "high": float("inf"), "low": float("-inf"), "change": float("nan")}
        response = NanSafeJSONResponse(data)
        body = json.loads(response.body)
        assert body["price"] == 100.0
        assert body["high"] is None
        assert body["low"] is None
        assert body["change"] is None

    def test_output_is_valid_json(self):
        data = {"prices": [float("nan"), 100.0, float("inf"), 200.0]}
        response = NanSafeJSONResponse(data)
        # json.loads will raise if the output is not valid JSON
        parsed = json.loads(response.body)
        assert isinstance(parsed, dict)
