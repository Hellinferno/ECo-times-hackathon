class BacktestingAgent:
    def evaluate_historical_signals(self, signal_res: dict, hist_data: list) -> dict:
        """
        Validates signal condition against 2-year prior data.
        Returns accuracy probability for generated opportunities.
        """
        if not hist_data or not signal_res.get("breakout_triggered"):
            # We simplify out pure volume logic for historicals constraints
            return {
                "backtest_matches": 0,
                "backtest_success_rate": 0.0,
                "backtest_avg_return": 0.0,
                "backtest_worst_case": 0.0,
                "backtest_best_case": 0.0,
                "cases": []
            }
            
        cases = []
        # Find structural historical breakouts logically 
        # (This is a simplified historical runner for Hackathon constraint)
        for i in range(30, len(hist_data) - 5):
            window = hist_data[i-30:i]
            res_level = max([x["close"] for x in window])
            current = hist_data[i]
            
            if current["close"] > res_level:
                # Historical trigger! measure T+5 outcome as per specification
                t5 = hist_data[i+5] if i+5 < len(hist_data) else hist_data[-1]
                ret_pct = ((t5["close"] - current["close"]) / current["close"]) * 100
                cases.append({
                    "date": current["date"],
                    "entry": current["close"],
                    "t5_exit": t5["close"],
                    "return_pct": ret_pct,
                    "success": ret_pct > 0
                })
        
        # Consider last 5 cases only as per specification
        recent_cases = cases[-5:] if len(cases) > 5 else cases
        matches = len(recent_cases)
        
        if matches == 0:
            return {
                "backtest_matches": 0,
                "backtest_success_rate": 0.0,
                "backtest_avg_return": 0.0,
                "backtest_worst_case": 0.0,
                "backtest_best_case": 0.0,
                "cases": []
            }
            
        successes = len([c for c in recent_cases if c["success"]])
        success_rate = (successes / matches) * 100
        returns = [c["return_pct"] for c in recent_cases]
        
        return {
            "backtest_matches": matches,
            "backtest_success_rate": round(success_rate, 2),
            "backtest_avg_return": round(sum(returns) / len(returns), 3),
            "backtest_worst_case": round(min(returns), 3),
            "backtest_best_case": round(max(returns), 3),
            "cases": recent_cases
        }
