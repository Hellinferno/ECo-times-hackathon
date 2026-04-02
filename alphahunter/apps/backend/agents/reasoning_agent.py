"""ReasoningAgent - LLM-backed narrative generator for scan results."""
from __future__ import annotations

import hashlib
import json
from typing import Optional

import redis as redis_lib

from config import settings
from loguru import logger

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover - exercised by fallback behavior
    genai = None
    types = None

_LLM_CACHE_TTL = 300
_PROMPT_VERSION = "reasoning-v2"
_REQUIRED_KEYS = ("llm_summary", "key_factors", "risk_warnings")

_llm_redis_client: Optional[redis_lib.Redis] = None


def _get_llm_redis() -> Optional[redis_lib.Redis]:
    """Return shared Redis client for LLM cache, or None if unavailable."""
    global _llm_redis_client
    if _llm_redis_client is not None:
        return _llm_redis_client
    try:
        client = redis_lib.from_url(
            settings.redis_url, decode_responses=True, socket_timeout=2
        )
        client.ping()
        _llm_redis_client = client
        return _llm_redis_client
    except Exception as exc:
        logger.debug(f"Redis unavailable for LLM cache: {exc}")
        return None


def _make_cache_key(model: str, prompt_context: str, prompt_version: str = _PROMPT_VERSION) -> str:
    """Build a cache key from the exact prompt content, model name, and prompt version."""
    digest = hashlib.sha256(
        f"{model}:{prompt_version}:{prompt_context}".encode()
    ).hexdigest()[:16]
    return f"llm:explanation:{digest}"


class ReasoningAgent:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self.max_output_tokens = settings.LLM_MAX_TOKENS
        self.client = None

        if self.api_key and genai is not None:
            self.client = genai.Client(api_key=self.api_key)
        elif self.api_key and genai is None:
            logger.warning("google-genai is not installed. Using fallback reasoning generator.")

    @staticmethod
    def _numeric_variants(value) -> set[str]:
        if value is None:
            return set()
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return {str(value)}
        variants = {
            str(value),
            str(int(numeric)) if numeric.is_integer() else "",
            f"{numeric:.1f}",
            f"{numeric:.2f}",
            f"{numeric:,.0f}",
            f"{numeric:,.1f}",
            f"{numeric:,.2f}",
        }
        return {variant for variant in variants if variant}

    def _decorate_output(
        self,
        payload: dict,
        *,
        source: str,
        validation_status: str = "passed",
        validation_errors: list[str] | None = None,
    ) -> dict:
        normalized = {
            "llm_summary": str(payload.get("llm_summary", "")).strip(),
            "key_factors": list(payload.get("key_factors", []))[:3],
            "risk_warnings": list(payload.get("risk_warnings", []))[:3],
        }
        normalized["metadata"] = {
            "source": source,
            "model_name": self.model,
            "prompt_version": _PROMPT_VERSION,
            "validation_status": validation_status,
            "validation_errors": validation_errors or [],
        }
        return normalized

    def _validate_output(self, result: dict, current_price: float, signals: dict, backtest: dict) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if not isinstance(result, dict):
            return False, ["result is not a dict"]

        for key in _REQUIRED_KEYS:
            if key not in result:
                errors.append(f"missing key: {key}")
        if errors:
            return False, errors
        if not isinstance(result.get("llm_summary"), str):
            errors.append("llm_summary must be a string")
        if not isinstance(result.get("key_factors"), list):
            errors.append("key_factors must be a list")
        if not isinstance(result.get("risk_warnings"), list):
            errors.append("risk_warnings must be a list")
        if errors:
            return False, errors

        text_blob = json.dumps(
            {
                "llm_summary": result.get("llm_summary"),
                "key_factors": result.get("key_factors"),
                "risk_warnings": result.get("risk_warnings"),
            },
            ensure_ascii=False,
        )
        normalized_blob = text_blob.replace(",", "")

        breakout = signals.get("breakout_details", {}) if signals.get("breakout_triggered") else {}
        volume = signals.get("volume_spike_details", {}) if signals.get("volume_spike_triggered") else {}
        bulk = signals.get("bulk_deal_details", {}) if signals.get("bulk_deal_triggered") else {}

        required_numeric_fields = [
            ("current_price", current_price),
            ("resistance_level", breakout.get("resistance_level")),
            ("pct_above", breakout.get("pct_above")),
            ("volume_ratio", volume.get("volume_ratio")),
            ("avg_volume_20d", volume.get("avg_volume_20d")),
            ("bulk_quantity", bulk.get("quantity")),
            ("bulk_price", bulk.get("price")),
        ]
        if backtest.get("backtest_matches", 0) > 0:
            required_numeric_fields.extend(
                [
                    ("backtest_success_rate", backtest.get("backtest_success_rate")),
                    ("backtest_avg_return", backtest.get("backtest_avg_return")),
                ]
            )

        for label, value in required_numeric_fields:
            if value is None:
                continue
            variants = self._numeric_variants(value)
            if not any((variant in text_blob) or (variant.replace(",", "") in normalized_blob) for variant in variants):
                errors.append(f"missing exact value for {label}")

        return len(errors) == 0, errors

    def generate_explanation(self, symbol: str, current_price: float, signals: dict, backtest: dict) -> dict:
        """Return a validated dict explanation grounded in signal data."""
        if sum([signals.get("breakout_triggered"), signals.get("volume_spike_triggered"), signals.get("bulk_deal_triggered")]) == 0:
            return self._decorate_output(
                {
                    "llm_summary": "No significant signals detected at this time.",
                    "key_factors": [],
                    "risk_warnings": [],
                },
                source="no_signal",
            )

        prompt_context = self._build_prompt_context(symbol, current_price, signals, backtest)

        if not self.client:
            logger.warning("Gemini API key not set. Using fallback reasoning generator.")
            return self._fallback_explanation(symbol, current_price, signals, backtest)

        cache_key = _make_cache_key(self.model, prompt_context)
        redis = _get_llm_redis()
        if redis:
            try:
                cached = redis.get(cache_key)
                if cached:
                    logger.debug(f"LLM cache hit for {symbol}")
                    cached_payload = json.loads(cached)
                    is_valid, errors = self._validate_output(cached_payload, current_price, signals, backtest)
                    if is_valid:
                        return self._decorate_output(cached_payload, source="cache")
                    logger.warning(f"Discarding cached reasoning for {symbol}: {errors}")
            except Exception:
                pass

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt_context,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are an expert quantitative analyst for Indian equity markets. "
                        "Analyse the given trading setup and respond with ONLY valid JSON - "
                        "no markdown, no code fences, no extra text. "
                        'Schema: {"llm_summary": "<2-3 sentences using exact data values>", '
                        '"key_factors": ["<factor 1>", "<factor 2>", "<factor 3>"], '
                        '"risk_warnings": ["<risk 1>", "<risk 2>"]}'
                    ),
                    temperature=0.2,
                    max_output_tokens=min(self.max_output_tokens, 512),
                ),
            )
            if response.text:
                raw = response.text.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                parsed = json.loads(raw)
                is_valid, errors = self._validate_output(parsed, current_price, signals, backtest)
                if isinstance(parsed, dict) and is_valid:
                    decorated = self._decorate_output(parsed, source="llm")
                    if redis:
                        try:
                            redis.setex(cache_key, _LLM_CACHE_TTL, json.dumps(parsed))
                        except Exception:
                            pass
                    return decorated
                logger.warning(f"Gemini output failed validation for {symbol}: {errors}")

            logger.warning("Gemini returned unexpected format. Using fallback reasoning generator.")
        except Exception as exc:
            logger.error(f"LLM Error: {exc}")

        return self._fallback_explanation(symbol, current_price, signals, backtest)

    def _build_prompt_context(self, symbol, current_price, signals, backtest) -> str:
        context = f"Stock: {symbol}\nCurrent Price: {current_price}\n"
        if signals.get("breakout_triggered"):
            breakout = signals.get("breakout_details", {})
            context += (
                f"- Breakout Signal: Price crossed {breakout.get('lookback_days')}-day resistance at "
                f"{breakout.get('resistance_level')}, currently {breakout.get('pct_above'):.1f}% above level.\n"
            )
        if signals.get("volume_spike_triggered"):
            volume = signals.get("volume_spike_details", {})
            context += (
                f"- Volume Spike Signal: Trading volume is {volume.get('volume_ratio'):.1f}x the 20-day average of "
                f"{volume.get('avg_volume_20d')}.\n"
            )
        if signals.get("bulk_deal_triggered"):
            bulk = signals.get("bulk_deal_details", {})
            context += (
                f"- Institutional Buy: {bulk.get('buyer')} bought {bulk.get('quantity')} shares at "
                f"{bulk.get('price')} on {bulk.get('latest_deal_date')}.\n"
            )

        matches = backtest.get("backtest_matches", 0)
        success_rate = backtest.get("backtest_success_rate", 0)
        avg_return = backtest.get("backtest_avg_return", 0)
        if matches > 0:
            context += (
                f"\nBacktest (Last {matches} occurrences of this pattern):\n"
                f"- Success Rate: {success_rate}%\n"
                f"- Avg Return: {avg_return}%\n"
            )
        return context

    def _fallback_explanation(self, symbol, current_price, signals, backtest) -> dict:
        """Template-based fallback when LLM is unavailable or validation fails."""
        summary = f"{symbol} presents a potential opportunity at Rs {current_price}. "
        key_factors = []
        risk_warnings = ["This analysis is template-generated (LLM unavailable or validation failed). Verify independently."]

        if signals.get("breakout_triggered"):
            breakout = signals.get("breakout_details", {})
            days = breakout.get("lookback_days", "N/A")
            resistance = breakout.get("resistance_level", "N/A")
            pct_above = breakout.get("pct_above", 0)
            summary += (
                f"The price has broken above its {days}-day resistance at {resistance} "
                f"and is {pct_above:.1f}% above that level. "
            )
            key_factors.append(f"Breakout above {days}-day resistance at {resistance}")

        if signals.get("volume_spike_triggered"):
            volume = signals.get("volume_spike_details", {})
            ratio = volume.get("volume_ratio", 0)
            avg_volume = volume.get("avg_volume_20d", 0)
            summary += f"Unusual volume at {float(ratio):.1f}x the 20-day average of {avg_volume}. "
            key_factors.append(f"Volume spike: {float(ratio):.1f}x 20-day average ({avg_volume})")

        if signals.get("bulk_deal_triggered"):
            bulk = signals.get("bulk_deal_details", {})
            buyer = bulk.get("buyer", "Institutional investor")
            quantity = bulk.get("quantity", "N/A")
            price = bulk.get("price", "N/A")
            key_factors.append(f"Bulk deal: {buyer} bought {quantity} shares at {price}")

        if backtest.get("backtest_matches", 0) > 0:
            success_rate = backtest.get("backtest_success_rate", 0)
            matches = backtest.get("backtest_matches", 0)
            avg_return = backtest.get("backtest_avg_return", 0)
            summary += (
                f"Historically, this pattern succeeded {success_rate}% of the time across {matches} occurrences "
                f"with an average return of {avg_return}%."
            )
            key_factors.append(f"Backtest: {success_rate}% success rate over {matches} patterns, avg return {avg_return}%")
        else:
            risk_warnings.append("Insufficient historical data to validate this pattern.")

        return self._decorate_output(
            {
                "llm_summary": summary.strip(),
                "key_factors": key_factors[:3],
                "risk_warnings": risk_warnings[:2],
            },
            source="fallback",
            validation_status="fallback",
        )
