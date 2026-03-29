"""BacktestingAgent — historical signal pattern validator.

Scans up to 2 years of OHLCV data looking for prior occurrences of the
same signal pattern (breakout, volume spike, bulk deal proxy, RSI, MACD)
and measures the T+5 outcome at each occurrence.

Returns a backtest summary dict with:
  backtest_matches       Number of historical analogue cases found
  backtest_success_rate  Percentage that were profitable
  backtest_avg_return    Mean return across all measured cases
  backtest_worst_case    Minimum observed return (downside bound)
  backtest_best_case     Maximum observed return (upside cap)
  cases                  List of individual case records
"""
from __future__ import annotations

from typing import Any, Dict, List


_EMPTY_RESULT: Dict[str, Any] = {
    "backtest_matches": 0,
    "backtest_success_rate": 0.0,
    "backtest_avg_return": 0.0,
    "backtest_worst_case": 0.0,
    "backtest_best_case": 0.0,
    "cases": [],
}


def _summarise_cases(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    recent = cases[-5:] if len(cases) > 5 else cases
    if not recent:
        return dict(_EMPTY_RESULT)
    returns = [c["return_pct"] for c in recent]
    successes = sum(1 for r in returns if r > 0)
    return {
        "backtest_matches": len(recent),
        "backtest_success_rate": round((successes / len(recent)) * 100, 2),
        "backtest_avg_return": round(sum(returns) / len(returns), 3),
        "backtest_worst_case": round(min(returns), 3),
        "backtest_best_case": round(max(returns), 3),
        "cases": recent,
    }


def _t5_return(hist_data: list, trigger_idx: int) -> float:
    exit_idx = min(trigger_idx + 5, len(hist_data) - 1)
    entry = hist_data[trigger_idx]["close"]
    exit_price = hist_data[exit_idx]["close"]
    return ((exit_price - entry) / entry) * 100 if entry > 0 else 0.0


class BacktestingAgent:
    def evaluate_historical_signals(self, signal_res: dict, hist_data: list) -> dict:
        """
        Validates signal conditions against 2-year prior OHLCV data.
        Routes to the appropriate analogue finder based on which signals triggered.
        Returns the best available backtest result (breakout > volume > RSI > MACD > bulk).
        """
        if not hist_data or len(hist_data) < 36:
            return dict(_EMPTY_RESULT)

        # Priority order: breakout is most reliable, then volume, RSI, MACD, bulk
        if signal_res.get("breakout_triggered"):
            result = self._find_breakout_analogues(hist_data)
            if result["backtest_matches"] > 0:
                return result

        if signal_res.get("volume_spike_triggered"):
            ratio = (signal_res.get("volume_spike_details") or {}).get("volume_ratio", 2.0)
            result = self._find_volume_spike_analogues(hist_data, ratio)
            if result["backtest_matches"] > 0:
                return result

        if signal_res.get("rsi_triggered"):
            rsi_val = (signal_res.get("rsi_details") or {}).get("rsi", 40.0)
            result = self._find_rsi_analogues(hist_data, rsi_val)
            if result["backtest_matches"] > 0:
                return result

        if signal_res.get("macd_triggered"):
            result = self._find_macd_analogues(hist_data)
            if result["backtest_matches"] > 0:
                return result

        if signal_res.get("bulk_deal_triggered"):
            result = self._find_bulk_deal_proxy_analogues(hist_data)
            if result["backtest_matches"] > 0:
                return result

        return dict(_EMPTY_RESULT)

    # ── Analogue finders ──────────────────────────────────────────────────────

    def _find_breakout_analogues(self, hist_data: list, lookback: int = 30) -> dict:
        """Find historical 30-day resistance breakout patterns."""
        cases = []
        for i in range(lookback, len(hist_data) - 5):
            window_closes = [x["close"] for x in hist_data[i - lookback: i]]
            resistance = max(window_closes)
            if hist_data[i]["close"] > resistance:
                cases.append({
                    "date": hist_data[i]["date"],
                    "entry": hist_data[i]["close"],
                    "t5_exit": hist_data[min(i + 5, len(hist_data) - 1)]["close"],
                    "return_pct": _t5_return(hist_data, i),
                    "success": _t5_return(hist_data, i) > 0,
                    "pattern": "breakout",
                })
        return _summarise_cases(cases)

    def _find_volume_spike_analogues(self, hist_data: list, min_ratio: float = 2.0) -> dict:
        """Find historical volume spike patterns at or above the current ratio."""
        cases = []
        for i in range(20, len(hist_data) - 5):
            recent_vols = [x["volume"] for x in hist_data[i - 20: i]]
            avg_vol = sum(recent_vols) / len(recent_vols) if recent_vols else 0
            if avg_vol == 0:
                continue
            current_vol = hist_data[i]["volume"]
            ratio = current_vol / avg_vol
            # Match patterns with at least 80% of current ratio (similar magnitude)
            if ratio >= max(min_ratio * 0.80, 1.5):
                cases.append({
                    "date": hist_data[i]["date"],
                    "entry": hist_data[i]["close"],
                    "t5_exit": hist_data[min(i + 5, len(hist_data) - 1)]["close"],
                    "return_pct": _t5_return(hist_data, i),
                    "success": _t5_return(hist_data, i) > 0,
                    "pattern": "volume_spike",
                    "volume_ratio": round(ratio, 2),
                })
        return _summarise_cases(cases)

    def _find_rsi_analogues(self, hist_data: list, current_rsi: float, period: int = 14) -> dict:
        """Find historical periods where RSI was in the same zone as current RSI."""
        closes = [x["close"] for x in hist_data]
        rsi_values = self._compute_rsi_series(closes, period)
        # rsi_values[i] corresponds to hist_data[i + period]
        rsi_zone_low = max(current_rsi - 5, 10)
        rsi_zone_high = min(current_rsi + 5, 45)

        cases = []
        for j, rsi_val in enumerate(rsi_values):
            i = j + period  # index into hist_data
            if i >= len(hist_data) - 5:
                break
            if rsi_zone_low <= rsi_val <= rsi_zone_high:
                cases.append({
                    "date": hist_data[i]["date"],
                    "entry": hist_data[i]["close"],
                    "t5_exit": hist_data[min(i + 5, len(hist_data) - 1)]["close"],
                    "return_pct": _t5_return(hist_data, i),
                    "success": _t5_return(hist_data, i) > 0,
                    "pattern": "rsi_oversold",
                    "rsi": round(rsi_val, 2),
                })
        return _summarise_cases(cases)

    def _find_macd_analogues(self, hist_data: list, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
        """Find historical MACD bullish crossovers."""
        closes = [x["close"] for x in hist_data]
        min_len = slow + signal
        if len(closes) < min_len + 5:
            return dict(_EMPTY_RESULT)

        def _ema(prices: list, p: int) -> list:
            k = 2.0 / (p + 1)
            ema = [prices[0]]
            for price in prices[1:]:
                ema.append(price * k + ema[-1] * (1 - k))
            return ema

        ema_fast = _ema(closes, fast)
        ema_slow = _ema(closes, slow)
        macd_line = [ema_fast[i] - ema_slow[i] for i in range(len(ema_slow))]
        macd_valid = macd_line[slow - 1:]
        signal_line = _ema(macd_valid, signal)

        cases = []
        for j in range(1, len(signal_line) - 5):
            # Bullish crossover: previous bar macd <= signal, current bar macd > signal
            if macd_valid[j - 1] <= signal_line[j - 1] and macd_valid[j] > signal_line[j]:
                i = j + (slow - 1)  # index into hist_data
                if i >= len(hist_data) - 5:
                    break
                cases.append({
                    "date": hist_data[i]["date"],
                    "entry": hist_data[i]["close"],
                    "t5_exit": hist_data[min(i + 5, len(hist_data) - 1)]["close"],
                    "return_pct": _t5_return(hist_data, i),
                    "success": _t5_return(hist_data, i) > 0,
                    "pattern": "macd_crossover",
                })
        return _summarise_cases(cases)

    def _find_bulk_deal_proxy_analogues(self, hist_data: list) -> dict:
        """
        Proxy for bulk deal signals: find days with unusually high volume AND price
        gap-up (>1% from previous close), as a rough institutional-activity proxy.
        """
        cases = []
        for i in range(20, len(hist_data) - 5):
            recent_vols = [x["volume"] for x in hist_data[i - 20: i]]
            avg_vol = sum(recent_vols) / len(recent_vols) if recent_vols else 0
            if avg_vol == 0:
                continue
            current = hist_data[i]
            prev_close = hist_data[i - 1]["close"]
            vol_ratio = current["volume"] / avg_vol
            price_gap = (current["close"] - prev_close) / prev_close if prev_close > 0 else 0

            if vol_ratio >= 1.8 and price_gap >= 0.01:
                cases.append({
                    "date": current["date"],
                    "entry": current["close"],
                    "t5_exit": hist_data[min(i + 5, len(hist_data) - 1)]["close"],
                    "return_pct": _t5_return(hist_data, i),
                    "success": _t5_return(hist_data, i) > 0,
                    "pattern": "institutional_proxy",
                    "volume_ratio": round(vol_ratio, 2),
                    "price_gap_pct": round(price_gap * 100, 2),
                })
        return _summarise_cases(cases)

    # ── Helper ─────────────────────────────────────────────────────────────────

    def _compute_rsi_series(self, closes: list, period: int = 14) -> list:
        """Compute RSI for every point from index `period` onward."""
        if len(closes) < period + 1:
            return []
        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        gains = [max(d, 0.0) for d in deltas]
        losses = [max(-d, 0.0) for d in deltas]

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        rsi_series: list[float] = []

        rs = avg_gain / avg_loss if avg_loss > 0 else float("inf")
        rsi_series.append(100.0 - (100.0 / (1.0 + rs)) if avg_loss > 0 else 100.0)

        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            rs = avg_gain / avg_loss if avg_loss > 0 else float("inf")
            rsi_series.append(100.0 - (100.0 / (1.0 + rs)) if avg_loss > 0 else 100.0)

        return rsi_series
