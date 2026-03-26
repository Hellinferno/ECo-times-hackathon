from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models.db import ScanRun, Stock
from agents import DataAgent, SignalAgent, BacktestingAgent, ReasoningAgent, DecisionAgent, AuditAgent
from loguru import logger
from database import SessionLocal

router = APIRouter()

def execute_pipeline(scan_run_id: int, symbols: list):
    """The synchronous multi-agent orchestration loop per stock."""
    db = SessionLocal()
    try:
        scan_run = db.query(ScanRun).get(scan_run_id)
        if not scan_run:
            return

        data_agent = DataAgent(db)
        signal_agent = SignalAgent()
        backtesting_agent = BacktestingAgent()
        reasoning_agent = ReasoningAgent()
        decision_agent = DecisionAgent()
        audit_agent = AuditAgent(db)

        signals_found = 0
        stocks_scanned = 0

        for symbol in symbols:
            # Phase 1: Data Fetching
            market_data = data_agent.get_market_data(symbol)
            if not market_data:
                continue

            bulk_deals = data_agent.get_bulk_deals(symbol)

            # Phase 2: Signal Detection
            signal_data = signal_agent.detect_signals(market_data, bulk_deals)

            if signal_data["signal_count"] > 0:
                signals_found += 1

                # Phase 2b: Backtesting validation
                hist_data = data_agent.get_historical_data_for_backtest(symbol)
                bt_results = backtesting_agent.evaluate_historical_signals(signal_data, hist_data)

                signal_data.update(bt_results)

                # Phase 2c: Natural Language Reasoning
                reasoning = reasoning_agent.generate_explanation(
                    symbol, market_data["current_price"], signal_data, bt_results
                )

                # Phase 2d: Confidence & Parameters
                decision = decision_agent.evaluate(
                    market_data["current_price"],
                    signal_data["composite_score"],
                    bt_results,
                    signal_data
                )

                snapshot = {
                    "market_data": market_data,
                    "bulk_deals": bulk_deals,
                    "signals": signal_data,
                    "backtest_results": bt_results,
                    "reasoning": reasoning,
                    "decision_metrics": decision
                }

                # Audit & Persist
                result_id = audit_agent.log_scan_result(scan_run_id, signal_data, reasoning)
                if result_id:
                    audit_agent.log_decision(result_id, symbol, decision, snapshot)

            stocks_scanned += 1

        # Update Run tracking
        scan_run.status = "completed"
        scan_run.completed_at = datetime.utcnow()
        scan_run.stocks_scanned = stocks_scanned
        scan_run.signals_found = signals_found
        scan_run.duration_secs = (scan_run.completed_at - scan_run.started_at).total_seconds()
        db.commit()
    except Exception as e:
        logger.error(f"Pipeline crashed mid-run: {e}")
        db.rollback()
        scan_run = db.query(ScanRun).get(scan_run_id)
        if scan_run:
            scan_run.status = "failed"
            scan_run.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


@router.post("")
def trigger_scan(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """API endpoint to invoke full structural scan."""
    
    # Check for blocking
    active_run = db.query(ScanRun).filter(ScanRun.status == "running").first()
    if active_run:
        raise HTTPException(status_code=409, detail="A scan is already running. Please wait.")
        
    # Initialization track
    run = ScanRun(triggered_by="manual", status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    
    # Grab Active Trackers
    stocks = db.query(Stock.symbol).filter(Stock.is_active == True).all()
    symbols = [s[0] for s in stocks]

    # Offload Heavy computation block
    background_tasks.add_task(execute_pipeline, run.id, symbols)

    return {
        "success": True,
        "data": {
            "scan_run_id": str(run.run_id),
            "status": run.status,
            "started_at": run.started_at.isoformat(),
            "stocks_queued": len(symbols),
        }
    }
