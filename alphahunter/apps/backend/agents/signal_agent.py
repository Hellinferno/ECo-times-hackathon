import datetime
from typing import Any, Dict, List, Optional, Tuple


class SignalAgent:
    def __init__(
        self,
        breakout_lookback_days: int = 30,
        volume_spike_threshold: float = 2.0,
        bulk_deal_lookback_days: int = 5,
    ):
        self.breakout_lookback_days = breakout_lookback_days
        self.volume_spike_threshold = volume_spike_threshold
        self.bulk_deal_lookback_days = bulk_deal_lookback_days

    def detect_signals(
        self,
        market_data: dict,
        bulk_deals: list,
        external_context: Optional[Dict[str, Any]] = None,
        mode: str = "legacy",
    ) -> dict:
        """
        Runs technical + institutional + external signal detection.
        Modes:
        - legacy: use original 3-signal score.
        - shadow: compute both, but legacy score remains active.
        - active: grouped score drives decision unless all TinyFish-derived signals are unknown.
        """
        symbol = market_data["symbol"]
        current_price = market_data["current_price"]
        volume_today = market_data["volume_today"]
        ohlcv = market_data["ohlcv_short"]

        breakout_sig, breakout_det = self._detect_breakout(current_price, ohlcv)
        volume_sig, volume_det = self._detect_volume_spike(volume_today, ohlcv)
        bulk_sig, bulk_det = self._detect_bulk_deals(bulk_deals, current_price)

        news_sig, news_det, news_available = self._detect_news_sentiment(external_context)
        social_sig, social_det, social_available = self._detect_social_sentiment(external_context)
        insider_sig, insider_det, insider_available = self._detect_insider_filing(external_context)
        macro_sig, macro_det, macro_available = self._detect_macro_context(external_context)

        legacy_signal_count = sum([breakout_sig, volume_sig, bulk_sig])
        b_strength = breakout_det.get("strength", 0.0) if breakout_sig else 0.0
        v_strength = volume_det.get("strength", 0.0) if volume_sig else 0.0
        bulk_strength = bulk_det.get("strength", 0.0) if bulk_sig else 0.0
        legacy_composite = round((b_strength * 0.45) + (v_strength * 0.35) + (bulk_strength * 0.20), 4)

        technical_score = self._weighted_average(
            [
                {"available": True, "weight": 0.55, "strength": b_strength},
                {"available": True, "weight": 0.45, "strength": v_strength},
            ]
        )
        institutional_score = self._weighted_average(
            [
                {"available": True, "weight": 0.60, "strength": bulk_strength},
                {"available": insider_available, "weight": 0.40, "strength": insider_det.get("strength", 0.0)},
            ]
        )
        sentiment_macro_score = self._weighted_average(
            [
                {"available": news_available, "weight": 0.45, "strength": news_det.get("strength", 0.0)},
                {"available": social_available, "weight": 0.35, "strength": social_det.get("strength", 0.0)},
                {"available": macro_available, "weight": 0.20, "strength": macro_det.get("strength", 0.0)},
            ]
        )

        grouped_composite = self._weighted_average(
            [
                {"available": technical_score is not None, "weight": 0.45, "strength": technical_score or 0.0},
                {"available": institutional_score is not None, "weight": 0.30, "strength": institutional_score or 0.0},
                {"available": sentiment_macro_score is not None, "weight": 0.25, "strength": sentiment_macro_score or 0.0},
            ]
        )

        tinyfish_available = any([news_available, social_available, insider_available, macro_available])
        mode = (mode or "legacy").lower()
        if mode not in {"legacy", "shadow", "active"}:
            mode = "legacy"

        mode_effective = mode
        if mode == "active" and not tinyfish_available:
            mode_effective = "legacy_fallback"

        if mode_effective == "active":
            effective_composite = grouped_composite if grouped_composite is not None else legacy_composite
        else:
            effective_composite = legacy_composite

        extended_signal_count = sum(
            [
                breakout_sig,
                volume_sig,
                bulk_sig,
                news_sig if news_available else False,
                social_sig if social_available else False,
                insider_sig if insider_available else False,
                macro_sig if macro_available else False,
            ]
        )
        if mode_effective == "active":
            signal_count = extended_signal_count
            max_signal_count = 7
        else:
            signal_count = legacy_signal_count
            max_signal_count = 3

        extra_signals = {
            "news_sentiment": {
                "triggered": news_sig,
                "available": news_available,
                **news_det,
            },
            "social_sentiment": {
                "triggered": social_sig,
                "available": social_available,
                **social_det,
            },
            "insider_filing": {
                "triggered": insider_sig,
                "available": insider_available,
                **insider_det,
            },
            "macro_context": {
                "triggered": macro_sig,
                "available": macro_available,
                **macro_det,
            },
        }

        diagnostics = {
            "mode_requested": mode,
            "mode_effective": mode_effective,
            "legacy_composite_score": legacy_composite,
            "grouped_composite_score": grouped_composite,
            "group_scores": {
                "technical": technical_score,
                "institutional": institutional_score,
                "sentiment_macro": sentiment_macro_score,
            },
            "data_availability": {
                "news_sentiment": news_available,
                "social_sentiment": social_available,
                "insider_filing": insider_available,
                "macro_context": macro_available,
            },
        }

        return {
            "symbol": symbol,
            "breakout_triggered": breakout_sig,
            "breakout_details": breakout_det,
            "volume_spike_triggered": volume_sig,
            "volume_spike_details": volume_det,
            "bulk_deal_triggered": bulk_sig,
            "bulk_deal_details": bulk_det,
            "news_sentiment_triggered": news_sig,
            "social_sentiment_triggered": social_sig,
            "insider_filing_triggered": insider_sig,
            "macro_context_triggered": macro_sig,
            "signal_count": signal_count,
            "max_signal_count": max_signal_count,
            "composite_score": round(effective_composite, 4),
            "legacy_composite_score": legacy_composite,
            "grouped_composite_score": grouped_composite,
            "extra_signals": extra_signals,
            "signal_diagnostics": diagnostics,
        }

    def _detect_breakout(self, current_price: float, ohlcv: list) -> Tuple[bool, Dict[str, Any]]:
        if len(ohlcv) < 5:
            return False, {"error": "Insufficient data", "strength": 0.0}

        recent_closes = [day["close"] for day in ohlcv[-self.breakout_lookback_days : -1]]
        if not recent_closes:
            return False, {"strength": 0.0}

        resistance_level = max(recent_closes)
        breakout_triggered = current_price > resistance_level
        pct_above = ((current_price - resistance_level) / resistance_level) * 100 if resistance_level > 0 else 0

        strength = 0.0
        if breakout_triggered:
            raw_strength = min(pct_above / 5.0, 1.0)
            recency_bonus = 0.15
            strength = min(raw_strength + recency_bonus, 1.0)

        details = {
            "resistance_level": float(resistance_level),
            "pct_above": float(pct_above),
            "strength": float(strength),
            "lookback_days": self.breakout_lookback_days,
        }
        return breakout_triggered, details

    def _detect_volume_spike(self, volume_today: int, ohlcv: list) -> Tuple[bool, Dict[str, Any]]:
        if len(ohlcv) < 20:
            return False, {"error": "Insufficient data", "strength": 0.0}

        recent_volumes = [day["volume"] for day in ohlcv[-20:-1]]
        avg_volume_20d = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
        if avg_volume_20d == 0:
            return False, {"strength": 0.0}

        volume_ratio = volume_today / avg_volume_20d
        volume_spike_triggered = volume_ratio >= self.volume_spike_threshold

        strength = 0.0
        if volume_spike_triggered:
            max_ratio = 4.0
            strength = min((volume_ratio - self.volume_spike_threshold) / (max_ratio - self.volume_spike_threshold), 1.0)
            strength = max(strength, 0.1)

        details = {
            "avg_volume_20d": float(avg_volume_20d),
            "volume_ratio": float(volume_ratio),
            "strength": float(strength),
        }
        return volume_spike_triggered, details

    def _detect_bulk_deals(self, bulk_deals: list, current_price: float) -> Tuple[bool, Dict[str, Any]]:
        if not bulk_deals:
            return False, {"strength": 0.0}

        cutoff = datetime.date.today() - datetime.timedelta(days=self.bulk_deal_lookback_days)
        recent_buys = []
        for deal in bulk_deals:
            deal_type = str(deal.get("deal_type", "")).upper()
            if deal_type != "BUY":
                continue
            deal_date_str = deal.get("date")
            try:
                deal_date = datetime.datetime.strptime(deal_date_str, "%Y-%m-%d").date()
            except Exception:
                continue
            if deal_date >= cutoff:
                recent_buys.append(deal)

        triggered = len(recent_buys) > 0
        if not triggered:
            return False, {"strength": 0.0}

        biggest_deal = max(recent_buys, key=lambda x: x.get("quantity", 0))
        details = {
            "latest_deal_date": biggest_deal.get("date"),
            "buyer": biggest_deal.get("client_name"),
            "price": biggest_deal.get("price"),
            "quantity": biggest_deal.get("quantity"),
            "strength": 1.0,
            "lookback_days": self.bulk_deal_lookback_days,
        }
        return True, details

    def _detect_news_sentiment(
        self, external_context: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Dict[str, Any], bool]:
        node = (external_context or {}).get("news_sentiment") or {}
        available = bool(node.get("available"))
        if not available:
            return False, {"status": "unknown", "strength": 0.0}, False

        weighted_sentiment = float(node.get("weighted_sentiment") or 0.0)
        article_count = int(node.get("article_count") or 0)
        triggered = article_count >= 2 and weighted_sentiment >= 0.25
        strength = min(max((weighted_sentiment - 0.25) / 0.75, 0.0), 1.0) if triggered else 0.0
        return (
            triggered,
            {
                "article_count": article_count,
                "weighted_sentiment": weighted_sentiment,
                "avg_confidence": node.get("avg_confidence"),
                "strength": round(strength, 4),
            },
            True,
        )

    def _detect_social_sentiment(
        self, external_context: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Dict[str, Any], bool]:
        node = (external_context or {}).get("social_sentiment") or {}
        available = bool(node.get("available"))
        if not available:
            return False, {"status": "unknown", "strength": 0.0}, False

        mention_zscore = float(node.get("mention_zscore") or 0.0)
        positive_ratio = float(node.get("positive_ratio") or 0.0)
        triggered = mention_zscore >= 2.0 and positive_ratio >= 0.60
        z_component = min(max((mention_zscore - 2.0) / 3.0, 0.0), 1.0)
        ratio_component = min(max((positive_ratio - 0.60) / 0.40, 0.0), 1.0)
        strength = ((z_component * 0.6) + (ratio_component * 0.4)) if triggered else 0.0
        return (
            triggered,
            {
                "mention_zscore": mention_zscore,
                "positive_ratio": positive_ratio,
                "sample_count": int(node.get("sample_count") or 0),
                "strength": round(strength, 4),
            },
            True,
        )

    def _detect_insider_filing(
        self, external_context: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Dict[str, Any], bool]:
        node = (external_context or {}).get("insider_filing") or {}
        available = bool(node.get("available"))
        if not available:
            return False, {"status": "unknown", "strength": 0.0}, False

        score = float(node.get("positive_filing_score") or 0.0)
        triggered = score >= 0.50
        strength = min(max((score - 0.50) / 0.50, 0.0), 1.0) if triggered else 0.0
        return (
            triggered,
            {
                "positive_filing_score": score,
                "filing_count": int(node.get("filing_count") or 0),
                "strength": round(strength, 4),
            },
            True,
        )

    def _detect_macro_context(
        self, external_context: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Dict[str, Any], bool]:
        node = (external_context or {}).get("macro_indicator") or {}
        available = bool(node.get("available"))
        if not available:
            return False, {"status": "unknown", "strength": 0.0}, False

        score = float(node.get("sector_macro_score") or 0.0)
        freshness_minutes = float(node.get("freshness_minutes") or 1e9)
        triggered = score >= 0.30 and freshness_minutes <= 60
        score_component = min(max((score - 0.30) / 0.70, 0.0), 1.0)
        freshness_component = min(max((60 - freshness_minutes) / 60, 0.0), 1.0)
        strength = (score_component * 0.7 + freshness_component * 0.3) if triggered else 0.0
        return (
            triggered,
            {
                "sector_macro_score": score,
                "freshness_minutes": freshness_minutes,
                "strength": round(strength, 4),
            },
            True,
        )

    def _weighted_average(self, components: List[Dict[str, Any]]) -> Optional[float]:
        weighted = 0.0
        weight_sum = 0.0
        for component in components:
            if not component.get("available", False):
                continue
            weight = float(component.get("weight", 0.0))
            strength = float(component.get("strength", 0.0))
            weighted += weight * strength
            weight_sum += weight
        if weight_sum == 0:
            return None
        return round(weighted / weight_sum, 4)
