import math

class SignalAgent:
    def __init__(self, breakout_lookback_days: int = 30, volume_spike_threshold: float = 2.0, bulk_deal_lookback_days: int = 5):
        self.breakout_lookback_days = breakout_lookback_days
        self.volume_spike_threshold = volume_spike_threshold
        self.bulk_deal_lookback_days = bulk_deal_lookback_days

    def detect_signals(self, market_data: dict, bulk_deals: list) -> dict:
        """
        Takes data from DataAgent and runs signal detection.
        Returns a dictionary with triggered signals, details, and score.
        """
        symbol = market_data["symbol"]
        current_price = market_data["current_price"]
        volume_today = market_data["volume_today"]
        ohlcv = market_data["ohlcv_short"]

        breakout_sig, breakout_det = self._detect_breakout(current_price, ohlcv)
        volume_sig, volume_det = self._detect_volume_spike(volume_today, ohlcv)
        bulk_sig, bulk_det = self._detect_bulk_deals(bulk_deals, current_price)

        signal_count = sum([breakout_sig, volume_sig, bulk_sig])
        
        # Calculate composite score based on individual algorithm strengths
        b_strength = breakout_det.get("strength", 0) if breakout_sig else 0
        v_strength = volume_det.get("strength", 0) if volume_sig else 0
        bulk_strength = bulk_det.get("strength", 0) if bulk_sig else 0

        # Weights: Breakout (0.45) + Volume (0.35) + Bulk Deal (0.2)
        composite_score = (b_strength * 0.45) + (v_strength * 0.35) + (bulk_strength * 0.20)

        return {
            "symbol": symbol,
            "breakout_triggered": breakout_sig,
            "breakout_details": breakout_det,
            "volume_spike_triggered": volume_sig,
            "volume_spike_details": volume_det,
            "bulk_deal_triggered": bulk_sig,
            "bulk_deal_details": bulk_det,
            "signal_count": signal_count,
            "composite_score": round(composite_score, 4)
        }

    def _detect_breakout(self, current_price: float, ohlcv: list):
        if len(ohlcv) < 5:
            return False, {"error": "Insufficient data"}
            
        recent_closes = [day["close"] for day in ohlcv[-self.breakout_lookback_days:-1]]
        if not recent_closes:
            return False, {}
            
        resistance_level = max(recent_closes)
        breakout_triggered = current_price > resistance_level
        pct_above = ((current_price - resistance_level) / resistance_level) * 100 if resistance_level > 0 else 0
        
        strength = 0.0
        if breakout_triggered:
            raw_strength = min(pct_above / 5.0, 1.0)
            recency_bonus = 0.15 # Assuming freshly triggered today
            strength = min(raw_strength + recency_bonus, 1.0)
            
        details = {
            "resistance_level": float(resistance_level),
            "pct_above": float(pct_above),
            "strength": float(strength),
            "lookback_days": self.breakout_lookback_days
        }
        return breakout_triggered, details

    def _detect_volume_spike(self, volume_today: int, ohlcv: list):
        if len(ohlcv) < 20:
            return False, {"error": "Insufficient data"}
            
        recent_volumes = [day["volume"] for day in ohlcv[-20:-1]]
        avg_volume_20d = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
        
        if avg_volume_20d == 0:
            return False, {}
            
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
            "strength": float(strength)
        }
        return volume_spike_triggered, details

    def _detect_bulk_deals(self, bulk_deals: list, current_price: float):
        if not bulk_deals:
            return False, {}
            
        recent_buys = [d for d in bulk_deals if d["deal_type"] == "BUY"]
        triggered = len(recent_buys) > 0
        
        strength = 0.0
        details = {}
        if triggered:
            strength = 1.0 # Boolean signal logic (1.0 if happened)
            # Find the most relevant buyer
            biggest_deal = max(recent_buys, key=lambda x: x["quantity"])
            details = {
                "latest_deal_date": biggest_deal["date"],
                "buyer": biggest_deal["client_name"],
                "price": biggest_deal["price"],
                "quantity": biggest_deal["quantity"],
                "strength": strength
            }
            
        return triggered, details
