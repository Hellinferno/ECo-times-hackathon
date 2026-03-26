import json
from datetime import datetime
from database import SessionLocal
from models.db import ScanRun, ScanResult, Decision, Stock
from agents.audit_agent import AuditAgent
import uuid

def seed_mock_opportunity():
    db = SessionLocal()
    
    # Check if we have anything to act upon
    stock = db.query(Stock).filter(Stock.symbol == "INFY").first()
    if not stock:
        print("No stock found.")
        return

    # Create dummy scan run
    run = ScanRun(triggered_by="demo_script", status="completed", completed_at=datetime.utcnow(), stocks_scanned=1, signals_found=1)
    db.add(run)
    db.commit()
    db.refresh(run)

    # Mock signals
    signals = {
        "symbol": "INFY",
        "composite_score": 0.85,
        "signal_count": 2,
        "breakout_triggered": True,
        "breakout_details": {"resistance_level": 1400.0, "pct_above": 5.2, "strength": 0.8},
        "volume_spike_triggered": True,
        "volume_spike_details": {"volume_ratio": 3.5, "strength": 0.9},
        "bulk_deal_triggered": False,
        "bulk_deal_details": {}
    }

    # Mock reasoning
    reasoning = {
        "llm_summary": "INFY has demonstrated a sharp price breakout accompanied by a 3.5x volume expansion. Historical backtesting of similar volatile patterns suggests a high probability of continued upward momentum. The fundamentals align with a bullish continuation structure.",
        "key_factors": ["3.5x Volume Expansion", "Broke 30-day resistance at 1400", "Historical win rate 68%"],
        "risk_warnings": ["Sector-wide pullback risk", "Pending earnings decay"],
        "confidence_score": 88
    }

    # Mock Decision
    decision = {
        "action": "BUY",
        "confidence": 85.0,
        "entry_price": 1410.0,
        "target_price": 1600.0,
        "stop_loss": 1390.0,
        "rr_ratio": 2.5,
        "score_signal": 0.85,
        "score_backtest": 0.78,
        "score_composite": 0.82
    }

    snapshot = {
        "signals": signals,
        "reasoning": reasoning,
        "decision": decision
    }

    audit_agent = AuditAgent(db)
    
    result_id = audit_agent.log_scan_result(run.id, signals, json.dumps(reasoning))
    
    if result_id:
        audit_agent.log_decision(result_id, "INFY", decision, snapshot)
        print("Successfully seeded a mock opportunity for INFY!")
    else:
        print("Failed to seed.")

if __name__ == "__main__":
    seed_mock_opportunity()
