import math
from typing import Dict, Any

class DecisionAgent:
    def evaluate(self, current_price: float, signal_score: float, backtest_data: dict, signal_details: dict) -> Dict[str, Any]:
        """
        Synthesizes strength factors and calculates strict confidence output & action parameters.
        Action logic maps to >=70% mapped to BUY, 50-69% WATCH, <50% AVOID
        """
        
        # Calculate Backtesting Score (Max 1.0)
        matches = backtest_data.get("backtest_matches", 0)
        if matches > 0:
            sr = backtest_data.get("backtest_success_rate", 0) / 100.0
            avg_ret = backtest_data.get("backtest_avg_return", 0)
            bt_score = sr * min(abs(avg_ret)/5.0, 1.0)
        else:
            bt_score = 0.0

        # Signal count bonus (max 1.0 for 3 signals)
        signal_count = signal_details.get("signal_count", 0)
        signal_count_score = min(signal_count / 3.0, 1.0)

        # Weights per spec: Signal 40%, Backtest 40%, Signal Count 20%
        if matches > 0:
            composite_score = (signal_score * 0.40) + (bt_score * 0.40) + (signal_count_score * 0.20)
        else:
            composite_score = (signal_score * 0.60) + (signal_count_score * 0.40)
            
        confidence = round(composite_score * 100, 2)
        
        # Action Determination
        if confidence >= 70.0:
            action = "BUY"
        elif confidence >= 50.0:
            action = "WATCH"
        else:
            action = "AVOID"
            
        # Target/Stop Loss Math for Buy Actions
        entry = None
        target = None
        sl = None
        rr = None
        
        if action in ["BUY", "WATCH"]:
            entry = current_price
            
            # Using recent resistance/support parameters to establish stops
            breakout_info = signal_details.get("breakout_details", {})
            if breakout_info and breakout_info.get("resistance_level"):
                support = breakout_info.get("resistance_level")
                # SL slightly below the broken resistance (which becomes support)
                sl_risk = current_price - support
                sl = current_price - max(sl_risk * 1.05, current_price * 0.015) 
            else:
                sl = current_price * 0.97 # Fallback 3%
                
            risk_amt = entry - sl
            # Target aims for 1:2.5 RR based on specified risk geometry
            rr_assigned = 2.5
            target = entry + (risk_amt * rr_assigned)
            rr = rr_assigned

        return {
            "action": action,
            "confidence": confidence,
            "entry_price": round(entry, 2) if entry else None,
            "target_price": round(target, 2) if target else None,
            "stop_loss": round(sl, 2) if sl else None,
            "rr_ratio": rr,
            "score_signal": round(signal_score, 4),
            "score_backtest": round(bt_score, 4),
            "score_composite": round(composite_score, 4)
        }
