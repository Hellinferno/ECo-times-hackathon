import time
from typing import Dict
from anthropic import Anthropic
from config import settings
from loguru import logger

class ReasoningAgent:
    def __init__(self):
        # We attempt configuration safely; fallbacks allow un-gated mock running
        self.api_key = settings.ANTHROPIC_API_KEY
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None

    def generate_explanation(self, symbol: str, current_price: float, signals: dict, backtest: dict) -> str:
        """
        Uses an LLM to generate a plain-English explanation linked to hard data values.
        """
        if sum([signals.get("breakout_triggered"), signals.get("volume_spike_triggered"), signals.get("bulk_deal_triggered")]) == 0:
            return "No significant signals detected at this time."

        prompt_context = self._build_prompt_context(symbol, current_price, signals, backtest)
        
        if not self.client:
            logger.warning("Anthropic API key not set. Using fallback reasoning generator.")
            return self._fallback_explanation(symbol, current_price, signals, backtest)

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=250,
                temperature=0.2,
                system="You are an expert quantitative analyst. Explain this trading setup in 3-4 plain English sentences using the exact data values provided. Do not use generic filler. Be specific and data-driven.",
                messages=[
                    {"role": "user", "content": prompt_context}
                ]
            )
            return response.content[0].text
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

    def _fallback_explanation(self, symbol, current_price, signals, backtest) -> str:
        expl = f"{symbol} presents a potential opportunity at {current_price}. "
        if signals.get("breakout_triggered"):
            expl += f"The price has broken above its {signals.get('breakout_details',{}).get('lookback_days')}-day resistance. "
        if signals.get("volume_spike_triggered"):
            expl += f"There is notable buying pressure with volume {signals.get('volume_spike_details',{}).get('volume_ratio'):.2f}x above average. "
        if backtest.get("backtest_matches", 0) > 0:
            expl += f"Historically, this pattern succeeded {backtest.get('backtest_success_rate')}% of the time in the last {backtest.get('backtest_matches')} occurrences."
        return expl
