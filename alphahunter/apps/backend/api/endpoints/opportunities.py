"""Opportunities endpoint — ranked trade recommendations from the latest scan run.

Routes:
  GET  ""              Paginated list filtered by action / signal / min_confidence
  GET  /{decision_id}  Full detail for one decision including pipeline snapshot

The "reference scan run" is the most-recent completed run; falls back to the
most-recent run of any status when no completed run exists yet.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from api.presenters import serialize_opportunity
from database import get_db
from models.db import Decision, ScanResult, ScanRun, Stock

router = APIRouter()

# ── Query helpers ─────────────────────────────────────────────────────────────

SIGNAL_FILTERS = {
    "breakout": ScanResult.breakout_triggered.is_(True),
    "volume_spike": ScanResult.volume_spike_triggered.is_(True),
    "bulk_deal": ScanResult.bulk_deal_triggered.is_(True),
}


# ── Routes ────────────────────────────────────────────────────────────────────


def get_reference_scan_run(db: Session) -> ScanRun | None:
    latest_completed = (
        db.query(ScanRun)
        .filter(ScanRun.status == "completed")
        .order_by(desc(ScanRun.completed_at), desc(ScanRun.started_at))
        .first()
    )
    if latest_completed:
        return latest_completed

    return db.query(ScanRun).order_by(desc(ScanRun.started_at)).first()


@router.get("/sectors")
def list_sectors(db: Session = Depends(get_db)):
    """Return distinct non-null sectors present in the active stock universe."""
    rows = (
        db.query(Stock.sector)
        .filter(Stock.sector.isnot(None), Stock.is_active.is_(True))
        .distinct()
        .order_by(Stock.sector)
        .all()
    )
    return {"success": True, "data": [row[0] for row in rows]}


@router.get("")
def list_opportunities(
    action: str | None = Query(default=None, description="BUY, WATCH, or AVOID"),
    signal: str | None = Query(default=None, description="breakout, volume_spike, bulk_deal"),
    sector: str | None = Query(default=None, description="e.g. Technology, Financial Services"),
    min_confidence: float = Query(default=0.0, ge=0.0, le=100.0),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Fetch ranked current opportunities from the latest reference scan run."""

    reference_run = get_reference_scan_run(db)
    if not reference_run:
        return {
            "success": True,
            "data": {
                "scan_run_id": None,
                "status": "idle",
                "scanned_at": None,
                "total": 0,
                "opportunities": [],
            },
        }

    base_query = (
        db.query(Decision, ScanResult, Stock)
        .join(ScanResult, Decision.scan_result_id == ScanResult.id)
        .join(Stock, Stock.symbol == Decision.symbol)
        .filter(ScanResult.scan_run_id == reference_run.id)
    )

    if action:
        base_query = base_query.filter(Decision.action == action.upper())

    if min_confidence > 0:
        base_query = base_query.filter(Decision.confidence >= min_confidence)

    if signal:
        signal_clause = SIGNAL_FILTERS.get(signal)
        if signal_clause is None:
            raise HTTPException(status_code=400, detail="Unsupported signal filter")
        base_query = base_query.filter(signal_clause)

    if sector:
        base_query = base_query.filter(Stock.sector == sector)

    total = base_query.count()

    rows = (
        base_query.order_by(desc(Decision.confidence), desc(Decision.decided_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    payload = [serialize_opportunity(decision, scan_result, stock) for decision, scan_result, stock in rows]

    return {
        "success": True,
        "data": {
            "scan_run_id": str(reference_run.run_id),
            "status": reference_run.status,
            "scanned_at": (
                reference_run.completed_at.isoformat()
                if reference_run.completed_at
                else reference_run.started_at.isoformat()
            ),
            "total": total,
            "opportunities": payload,
        },
    }


@router.get("/{decision_id}")
def get_opportunity_detail(decision_id: str, db: Session = Depends(get_db)):
    """Fetch detailed current opportunity data for a single decision."""

    try:
        parsed_decision_id = UUID(decision_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid decision id") from exc

    row = (
        db.query(Decision, ScanResult, Stock)
        .join(ScanResult, Decision.scan_result_id == ScanResult.id)
        .join(Stock, Stock.symbol == Decision.symbol)
        .filter(Decision.decision_id == parsed_decision_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    decision, scan_result, stock = row
    opportunity = serialize_opportunity(decision, scan_result, stock)
    opportunity["snapshot"] = decision.snapshot_json or {}

    return {"success": True, "data": opportunity}
