from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models.db import ScanRun, Decision

router = APIRouter()


@router.get("")
def get_decision_history(
    action: str = Query(None, description="Filter by action: BUY, WATCH, AVOID"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """Fetch decision history with outcome tracking."""
    query = db.query(Decision).order_by(desc(Decision.decided_at))

    if action:
        query = query.filter(Decision.action == action.upper())

    decisions = query.limit(limit).all()

    payload = []
    for d in decisions:
        payload.append({
            "decision_id": str(d.decision_id),
            "symbol": d.symbol,
            "action": d.action,
            "confidence": float(d.confidence),
            "entry_price": float(d.entry_price) if d.entry_price else None,
            "target_price": float(d.target_price) if d.target_price else None,
            "stop_loss": float(d.stop_loss) if d.stop_loss else None,
            "rr_ratio": float(d.rr_ratio) if d.rr_ratio else None,
            "decided_at": d.decided_at.isoformat(),
            "outcome_measured": d.outcome_measured,
            "outcome_return_pct": float(d.outcome_return_pct) if d.outcome_return_pct else None,
            "outcome_result": d.outcome_result,
        })

    # Compute track record stats
    measured = [d for d in decisions if d.outcome_measured]
    wins = [d for d in measured if d.outcome_result == "WIN"]
    win_rate = (len(wins) / len(measured) * 100) if measured else None
    avg_return = (
        sum(float(d.outcome_return_pct) for d in measured if d.outcome_return_pct) / len(measured)
        if measured else None
    )

    return {
        "success": True,
        "data": {
            "decisions": payload,
            "track_record": {
                "total_decisions": len(decisions),
                "measured": len(measured),
                "wins": len(wins),
                "win_rate": round(win_rate, 1) if win_rate is not None else None,
                "avg_return_pct": round(avg_return, 2) if avg_return is not None else None,
            }
        }
    }


@router.get("/scans")
def get_scan_history(limit: int = Query(50, le=200), db: Session = Depends(get_db)):
    """Fetch all historical scan runs and their summary statistics."""
    runs = db.query(ScanRun).order_by(desc(ScanRun.started_at)).limit(limit).all()

    payload = []
    for run in runs:
        payload.append({
            "id": run.id,
            "run_id": str(run.run_id),
            "triggered_by": run.triggered_by,
            "status": run.status,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "duration_secs": run.duration_secs,
            "stocks_scanned": run.stocks_scanned,
            "signals_found": run.signals_found,
        })

    return {"success": True, "data": payload}
