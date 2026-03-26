from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models.db import Stock, Decision, ScanResult
import json

router = APIRouter()


@router.get("/{symbol}")
def get_stock_detail(symbol: str, db: Session = Depends(get_db)):
    """Full stock detail with latest signals, reasoning, backtest, and decision."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    # Get latest decision for this stock
    decision = (
        db.query(Decision)
        .filter(Decision.symbol == symbol.upper())
        .order_by(desc(Decision.decided_at))
        .first()
    )

    # Get latest scan result for this stock
    scan_result = None
    if decision and decision.scan_result_id:
        scan_result = db.query(ScanResult).filter(ScanResult.id == decision.scan_result_id).first()

    # Parse reasoning
    parsed_reasoning = {}
    if scan_result and scan_result.reasoning_text:
        try:
            parsed_reasoning = json.loads(scan_result.reasoning_text)
        except (json.JSONDecodeError, TypeError):
            parsed_reasoning = {"llm_summary": scan_result.reasoning_text}

    stock_data = {
        "symbol": stock.symbol,
        "name": stock.name,
        "sector": stock.sector,
        "market_cap_cr": float(stock.market_cap_cr) if stock.market_cap_cr else None,
        "is_active": stock.is_active,
    }

    if not decision:
        return {
            "success": True,
            "data": {
                "stock": stock_data,
                "decision": None,
                "signals": None,
                "reasoning": None,
                "backtest": None,
            }
        }

    decision_data = {
        "decision_id": str(decision.decision_id),
        "action": decision.action,
        "confidence": float(decision.confidence),
        "entry_price": float(decision.entry_price) if decision.entry_price else None,
        "target_price": float(decision.target_price) if decision.target_price else None,
        "stop_loss": float(decision.stop_loss) if decision.stop_loss else None,
        "rr_ratio": float(decision.rr_ratio) if decision.rr_ratio else None,
        "score_signal": float(decision.score_signal) if decision.score_signal else None,
        "score_backtest": float(decision.score_backtest) if decision.score_backtest else None,
        "score_composite": float(decision.score_composite) if decision.score_composite else None,
        "decided_at": decision.decided_at.isoformat(),
        "outcome_measured": decision.outcome_measured,
        "outcome_return_pct": float(decision.outcome_return_pct) if decision.outcome_return_pct else None,
        "outcome_result": decision.outcome_result,
    }

    signals_data = None
    backtest_data = None
    if scan_result:
        signals_data = {
            "breakout": scan_result.breakout_triggered,
            "volume_spike": scan_result.volume_spike_triggered,
            "bulk_deal": scan_result.bulk_deal_triggered,
            "signal_count": scan_result.signal_count,
            "composite_score": float(scan_result.composite_score) if scan_result.composite_score else None,
            "price": float(scan_result.price) if scan_result.price else None,
            "volume_today": scan_result.volume_today,
            "volume_avg_20d": scan_result.volume_avg_20d,
            "volume_ratio": float(scan_result.volume_ratio) if scan_result.volume_ratio else None,
            "breakout_details": scan_result.breakout_details,
            "volume_spike_details": scan_result.volume_spike_details,
            "bulk_deal_details": scan_result.bulk_deal_details,
        }
        backtest_data = {
            "matches": scan_result.backtest_matches,
            "success_rate": float(scan_result.backtest_success_rate) if scan_result.backtest_success_rate else None,
            "avg_return": float(scan_result.backtest_avg_return) if scan_result.backtest_avg_return else None,
            "worst_case": float(scan_result.backtest_worst_case) if scan_result.backtest_worst_case else None,
            "best_case": float(scan_result.backtest_best_case) if scan_result.backtest_best_case else None,
            "cases": scan_result.backtest_cases_json,
        }

    return {
        "success": True,
        "data": {
            "stock": stock_data,
            "decision": decision_data,
            "signals": signals_data,
            "reasoning": parsed_reasoning,
            "backtest": backtest_data,
        }
    }
