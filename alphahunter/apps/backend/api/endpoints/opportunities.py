from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.db import Decision, ScanResult
from sqlalchemy import desc
import json

router = APIRouter()

@router.get("")
def list_opportunities(limit: int = Query(20, le=100), db: Session = Depends(get_db)):
    """Fetch actionable pipeline conclusions mappings to BUY/WATCH parameters."""

    # Subquery / Joining
    decisions = (
        db.query(Decision, ScanResult.reasoning_text)
        .join(ScanResult, Decision.scan_result_id == ScanResult.id)
        .order_by(desc(Decision.confidence))
        .limit(limit)
        .all()
    )

    payload = []
    for d, reason in decisions:
        try:
            parsed_reasoning = json.loads(reason) if reason else {}
        except:
            parsed_reasoning = {"llm_summary": reason}

        payload.append({
            "decision_id": str(d.decision_id),
            "symbol": d.symbol,
            "action": d.action,
            "confidence": d.confidence,
            "entry_price": d.entry_price,
            "target": d.target_price,
            "stop_loss": d.stop_loss,
            "rr_ratio": d.rr_ratio,
            "reasoning": parsed_reasoning,
            "timestamp": d.decided_at.isoformat()
        })
        
    return {
        "success": True,
        "data": payload
    }

@router.get("/{decision_id}")
def get_opportunity_detail(decision_id: str, db: Session = Depends(get_db)):
    """Fetch complete detail, audit snapshot and data for a single opportunity."""
    decision = db.query(Decision).filter(Decision.decision_id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    result = db.query(ScanResult).filter(ScanResult.id == decision.scan_result_id).first()

    try:
        parsed_reasoning = json.loads(result.reasoning_text) if result and result.reasoning_text else {}
    except:
        parsed_reasoning = {"llm_summary": result.reasoning_text if result else ""}

    return {
        "success": True,
        "data": {
            "decision": {
                "decision_id": str(decision.decision_id),
                "symbol": decision.symbol,
                "action": decision.action,
                "confidence": decision.confidence,
                "entry_price": decision.entry_price,
                "target": decision.target_price,
                "stop_loss": decision.stop_loss,
                "rr_ratio": decision.rr_ratio,
                "score_signal": decision.score_signal,
                "score_backtest": decision.score_backtest,
                "score_composite": decision.score_composite,
                "timestamp": decision.decided_at.isoformat(),
                "snapshot": decision.snapshot_json
            },
            "signals": {
                "breakout": result.breakout_triggered if result else False,
                "volume": result.volume_spike_triggered if result else False,
                "bulk": result.bulk_deal_triggered if result else False,
                "breakout_details": json.loads(result.breakout_details) if result and isinstance(result.breakout_details, str) else (result.breakout_details if result else {}),
                "volume_details": json.loads(result.volume_spike_details) if result and isinstance(result.volume_spike_details, str) else (result.volume_spike_details if result else {}),
                "bulk_details": json.loads(result.bulk_deal_details) if result and isinstance(result.bulk_deal_details, str) else (result.bulk_deal_details if result else {})
            },
            "reasoning": parsed_reasoning
        }
    }
