"""ReasoningAgent — LLM-backed narrative generator for scan results.

Uses the Google Gemini API (`google-genai`) to produce a short, structured
explanation grounded in signal data and backtest statistics.

Fallback behaviour (in order):
  1. Gemini available and configured → call LLM, parse JSON response
  2. API key set but `google-genai` not installed → warning + template text
  3. No API key configured → template text only

The module-level import guard (`try/except ImportError`) keeps the agent
importable in environments where `google-genai` is absent.
"""
from __future__ import annotations

from config import settings
from loguru import logger

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover - exercised by fallback behavior
    genai = None
    types = None


class ReasoningAgent:
    def __init__(self):
        # We attempt configuration safely; fallbacks allow un-gated mock running
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self.max_output_tokens = settings.LLM_MAX_TOKENS
        self.client = None

        if self.api_key and genai is not None:
            self.client = genai.Client(api_key=self.api_key)
        elif self.api_key and genai is None:
            logger.warning("google-genai is not installed. Using fallback reasoning generator.")

    def generate_explanation(self, symbol: str, current_price: float, signals: dict, backtest: dict) -> dict:
        """
        Uses an LLM to generate a structured JSON explanation grounded in signal data.

        Returns a dict with keys: llm_summary, key_factors, risk_warnings.
        Always returns a dict — never a bare string — so parse_reasoning() in
        presenters.py gets consistent input regardless of the code path taken.
        """
        if sum([signals.get("breakout_triggered"), signals.get("volume_spike_triggered"), signals.get("bulk_deal_triggered")]) == 0:
            return {
                "llm_summary": "No significant signals detected at this time.",
                "key_factors": [],
                "risk_warnings": [],
            }

        prompt_context = self._build_prompt_context(symbol, current_price, signals, backtest)

        if not self.client:
            logger.warning("Gemini API key not set. Using fallback reasoning generator.")
            return self._fallback_explanation(symbol, current_price, signals, backtest)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt_context,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are an expert quantitative analyst for Indian equity markets. "
                        "Analyse the given trading setup and respond with ONLY valid JSON — "
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
                import json
                raw = response.text.strip()
                # Strip markdown code fences if the model adds them despite instructions
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                parsed = json.loads(raw)
                if isinstance(parsed, dict) and "llm_summary" in parsed:
                    return parsed

            logger.warning("Gemini returned unexpected format. Using fallback reasoning generator.")
        except Exception as e:
            logger.error(f"LLM Error: {e}")

        return self._fallback_explanation(symbol, current_price, signals, backtest)

    def _build_prompt_context(self, symbol, current_price, signals, backtest) -> str:
        s = f"Stock: {symbol}\nCurrent Price: {current_price}\n"
        if signals.get("breakout_triggered"):
            b = signals.get("breakout_details", {})
            s += f"- Breakout Signal: Price crossed {b.get('lookback_days')}-day resistance at {b.get('resistance_level')}, currently {b.get('pct_above'):.1f}% above level.\n"
        if signals.get("volume_spike_triggered"):
            v = signals.get("volume_spike_details", {})
            s += f"- Volume Spike Signal: Trading volume is {v.get('volume_ratio'):.1f}x the 20-day average of {v.get('avg_volume_20d')}.\n"
        if signals.get("bulk_deal_triggered"):
            d = signals.get("bulk_deal_details", {})
            s += f"- Institutional Buy: {d.get('buyer')} bought {d.get('quantity')} shares at {d.get('price')} on {d.get('latest_deal_date')}.\n"
        
        m = backtest.get("backtest_matches", 0)
        sr = backtest.get("backtest_success_rate", 0)
        ar = backtest.get("backtest_avg_return", 0)
        
        if m > 0:
            s += f"\nBacktest (Last {m} occurrences of this pattern):\n- Success Rate: {sr}%\n- Avg Return: {ar}%\n"
        
        return s

    def _fallback_explanation(self, symbol, current_price, signals, backtest) -> dict:
        """Template-based fallback when LLM is unavailable. Returns the same dict schema."""
        summary = f"{symbol} presents a potential opportunity at ₹{current_price}. "
        key_factors = []
        risk_warnings = ["This analysis is template-generated (LLM unavailable). Verify independently."]

        if signals.get("breakout_triggered"):
            days = signals.get("breakout_details", {}).get("lookback_days", "N/A")
            summary += f"The price has broken above its {days}-day resistance. "
            key_factors.append(f"Price breakout above {days}-day resistance level")

        if signals.get("volume_spike_triggered"):
            ratio = signals.get("volume_spike_details", {}).get("volume_ratio", 0)
            try:
                summary += f"Unusual volume at {float(ratio):.1f}x the 20-day average. "
                key_factors.append(f"Volume spike: {float(ratio):.1f}x 20-day average")
            except (TypeError, ValueError):
                key_factors.append("Volume spike detected")

        if signals.get("bulk_deal_triggered"):
            buyer = signals.get("bulk_deal_details", {}).get("buyer", "Institutional investor")
            key_factors.append(f"Bulk deal: {buyer} activity detected")

        if backtest.get("backtest_matches", 0) > 0:
            sr = backtest.get("backtest_success_rate", 0)
            m = backtest.get("backtest_matches", 0)
            summary += f"Historically, this pattern succeeded {sr}% of the time across {m} occurrences."
            key_factors.append(f"Backtest: {sr}% success rate over {m} historical patterns")
        else:
            risk_warnings.append("Insufficient historical data to validate this pattern.")

        return {
            "llm_summary": summary.strip(),
            "key_factors": key_factors[:3],
            "risk_warnings": risk_warnings[:2],
        }
