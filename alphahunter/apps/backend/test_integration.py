"""Integration smoke test — runs the full multi-agent pipeline against live market data.

Iterates over 14 NSE blue-chip symbols and exercises:
  DataAgent → SignalAgent → BacktestingAgent → DecisionAgent

Prints per-symbol diagnostics to stdout. Intended to be run manually against
a live database (not in CI); use pytest -k test_integration to invoke.
"""
from database import SessionLocal
from agents import DataAgent, SignalAgent, BacktestingAgent, ReasoningAgent, DecisionAgent

def test_integration():
    db = SessionLocal()
    
    data_agent = DataAgent(db)
    signal_agent = SignalAgent()
    backtesting_agent = BacktestingAgent()
    reasoning_agent = ReasoningAgent()
    decision_agent = DecisionAgent()

    symbols = ['INFY', 'TCS', 'RELIANCE', 'HDFCBANK', 'TATASTEEL', 'ICICIBANK', 'SBIN', 'BHARTIARTL', 'ITC', 'WIPRO', 'HINDUNILVR', 'LT', 'AXISBANK', 'MARUTI']

    for symbol in symbols:
        print(f"\n--- Testing {symbol} ---")
        market_data = data_agent.get_market_data(symbol)
        if not market_data:
            print(f"[{symbol}] Failed to fetch market data.")
            continue
            
        bulk = data_agent.get_bulk_deals(symbol)
        
        signals = signal_agent.detect_signals(market_data, bulk)
        print(f"[{symbol}] Current Price: {market_data['current_price']}, Volume: {market_data['volume_today']}")
        print(f"[{symbol}] Breakout: {signals['breakout_triggered']} (Res: {signals['breakout_details'].get('resistance_level')})")
        print(f"[{symbol}] Volume Spike: {signals['volume_spike_triggered']}")
        print(f"[{symbol}] Composite Score: {signals['composite_score']}")

        if signals['signal_count'] > 0:
            hist_data = data_agent.get_historical_data_for_backtest(symbol)
            bt_results = backtesting_agent.evaluate_historical_signals(signals, hist_data)
            
            print(f"[{symbol}] Backtest Probability: {bt_results.get('historical_probability_pct', 0)}%")
            
            decision = decision_agent.evaluate(market_data['current_price'], signals['composite_score'], bt_results, signals)
            print(f"[{symbol}] Decision Action: {decision['action']}")
            print(f"[{symbol}] Target: {decision['target_price']}, Stop Loss: {decision['stop_loss']}")
        else:
            print(f"[{symbol}] No signals triggered.")

if __name__ == "__main__":
    test_integration()
