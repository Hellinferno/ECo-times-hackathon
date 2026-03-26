import json
import datetime
from loguru import logger
from agents.signal_agent import SignalAgent
from agents.data_agent import DataAgent

def test_signal_agent_mock():
    # Mocking data to simulate a perfect Breakout + Volume Spike scenario
    logger.info("Initializing SignalAgent for Mock Testing...")
    agent = SignalAgent()

    # Create dummy OHLCV (20+ days of data)
    # The agent looks at the last 20-30 days (excluding today which is index -1)
    # We will make the past 30 days hover around 100 with volumes ~10,000
    mock_ohlcv = []
    for i in range(35):
        mock_ohlcv.append({
            "date": f"2023-10-{i+1:02d}" if i < 30 else f"2023-11-{i-29:02d}",
            "open": 98.0,
            "high": 101.0,
            "low": 97.0,
            "close": 100.0,
            "volume": 10000
        })
    
    # Today's setup (Simulating a breakout above 100.0 and volume spike)
    # Current price = 110.0 (10% higher than max past 30 days)
    # Today's Volume = 50000 (5x the average of 10000)
    market_data = {
        "symbol": "MOCK_STOCK",
        "current_price": 110.0,
        "volume_today": 50000,
        "ohlcv_short": mock_ohlcv
    }
    
    # Mock bulk deal
    bulk_deals = [
        {
            "date": datetime.date.today().strftime("%Y-%m-%d"),
            "deal_type": "BUY",
            "client_name": "BIG WHALE CAPITAL",
            "price": 105.0,
            "quantity": 1000000
        }
    ]

    logger.info(f"Feeding Mock Market Data -> Current Price: {market_data['current_price']}, Volume: {market_data['volume_today']}")
    
    # Execute Signal Detection
    results = agent.detect_signals(market_data, bulk_deals)
    
    logger.info("--- SIGNAL AGENT RESULT ---")
    logger.info(json.dumps(results, indent=2))
    
    # Assertions / Validations
    assert results["breakout_triggered"] is True
    assert results["volume_spike_triggered"] is True
    assert results["bulk_deal_triggered"] is True
    assert results["composite_score"] > 0.5
    
    logger.success(f"Mock test passed! Composite Score derived: {results['composite_score']}")

if __name__ == "__main__":
    test_signal_agent_mock()
