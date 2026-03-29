"""History endpoint — decision log with filtering, stats, export, and detail.

Routes:
  GET  ""                  Paginated decision list + summary stats
                           Filters: action | outcome | symbol | from_date | to_date
  GET  /export             CSV export of filtered decisions (max 10 000 rows)
  GET  /scans              Paginated list of past ScanRun records
  GET  /{decision_id}      Full detail including signals, reasoning, backtest, outcome
"""
from __future__ import annotations

import csv
import io
from datetime import date, datetime, time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session

from api.presenters import (
    parse_reasoning,
    serialize_decision_entry,
    serialize_scan_run,
    serialize_backtest,
    summarize_signals,
)
from database import get_db
from models.db import Decision, ScanResult, ScanRun, Stock

router = APIRouter()


# ── Query helpers ──────────────────────────────────────────────────────────────

def apply_decision_filters(
    query,
    action: str | None,
    outcome: str | None,
    symbol: str | None,
    from_date: date | None,
    to_date: date | None,
):
    if action:
        query = query.filter(Decision.action == action.upper())

    if outcome:
        normalized = outcome.lower()
        if normalized == "pending":
            query = query.filter(Decision.outcome_measured.is_(False))
        elif normalized in {"profit", "win"}:
            query = query.filter(Decision.outcome_result == "WIN")
        elif normalized in {"loss", "lose"}:
            query = query.filter(Decision.outcome_result == "LOSS")
        elif normalized == "neutral":
            query = query.filter(Decision.outcome_result == "NEUTRAL")
        else:
            raise HTTPException(status_code=400, detail="Unsupported outcome filter")

    if symbol:
        query = query.filter(Decision.symbol == symbol.upper())

    if from_date:
        query = query.filter(Decision.decided_at >= datetime.combine(from_date, time.min))

    if to_date:
        query = query.filter(Decision.decided_at <= datetime.combine(to_date, time.max))

    return query


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("")
def get_decision_history(
    action: str | None = Query(default=None, description="BUY, WATCH, AVOID"),
    outcome: str | None = Query(default=None, description="profit, loss, neutral, pending"),
    symbol: str | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Fetch filtered decision history plus summary and pagination metadata."""

    base_query = db.query(Decision, Stock).join(Stock, Stock.symbol == Decision.symbol)
    filtered_query = apply_decision_filters(base_query, action, outcome, symbol, from_date, to_date)

    total = filtered_query.count()
    rows = (
        filtered_query.order_by(desc(Decision.decided_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    stats_query = db.query(
        func.count(Decision.id).label("total"),
        func.count(case((Decision.action == "BUY", 1))).label("buys"),
        func.count(case((Decision.outcome_measured.is_(True), 1))).label("measured"),
        func.count(case((Decision.outcome_result == "WIN", 1))).label("wins"),
        func.avg(case((Decision.outcome_measured.is_(True), Decision.outcome_return_pct))).label("avg_return"),
    ).join(Stock, Stock.symbol == Decision.symbol)
    stats_query = apply_decision_filters(stats_query, action, outcome, symbol, from_date, to_date)
    stats = stats_query.one()

    measured_count = stats.measured or 0
    win_count = stats.wins or 0
    summary = {
        "total_decisions": stats.total,
        "buy_decisions": stats.buys,
        "measured": measured_count,
        "wins": win_count,
        "win_rate_pct": round((win_count / measured_count * 100), 1) if measured_count else None,
        "avg_return_pct": round(float(stats.avg_return), 2) if stats.avg_return is not None else None,
    }

    payload = [serialize_decision_entry(decision, stock) for decision, stock in rows]

    return {
        "success": True,
        "data": {
            "summary": summary,
            "decisions": payload,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        },
    }


@router.get("/export")
def export_decision_history(
    action: str | None = Query(default=None),
    outcome: str | None = Query(default=None),
    symbol: str | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Export filtered decision history as CSV."""

    query = db.query(Decision, Stock).join(Stock, Stock.symbol == Decision.symbol)
    rows = apply_decision_filters(query, action, outcome, symbol, from_date, to_date).order_by(
        desc(Decision.decided_at)
    ).limit(10000)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "decision_id",
            "symbol",
            "name",
            "decided_at",
            "action",
            "confidence",
            "entry_price",
            "target_price",
            "stop_loss",
            "outcome_result",
            "outcome_return_pct",
        ]
    )

    for decision, stock in rows.all():
        writer.writerow(
            [
                str(decision.decision_id),
                decision.symbol,
                stock.name,
                decision.decided_at.isoformat() if decision.decided_at else "",
                decision.action,
                float(decision.confidence) if decision.confidence is not None else "",
                float(decision.entry_price) if decision.entry_price is not None else "",
                float(decision.target_price) if decision.target_price is not None else "",
                float(decision.stop_loss) if decision.stop_loss is not None else "",
                decision.outcome_result or "",
                float(decision.outcome_return_pct) if decision.outcome_return_pct is not None else "",
            ]
        )

    today_label = datetime.utcnow().strftime("%Y-%m-%d")
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="alphahunter_decisions_{today_label}.csv"'
        },
    )


@router.get("/scans")
def get_scan_history(limit: int = Query(default=50, le=200), db: Session = Depends(get_db)):
    runs = db.query(ScanRun).order_by(desc(ScanRun.started_at)).limit(limit).all()
    return {"success": True, "data": [serialize_scan_run(run) for run in runs]}


@router.get("/{decision_id}")
def get_decision_detail(decision_id: str, db: Session = Depends(get_db)):
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
        raise HTTPException(status_code=404, detail="Decision not found")

    decision, scan_result, stock = row
    snapshot = decision.snapshot_json or {}

    return {
        "success": True,
        "data": {
            "decision": serialize_decision_entry(decision, stock),
            "stock": {
                "symbol": stock.symbol,
                "name": stock.name,
                "sector": stock.sector,
            },
            "signals": summarize_signals(scan_result),
            "reasoning": parse_reasoning(scan_result.reasoning_text if scan_result else None),
            "backtest": serialize_backtest(scan_result),
            "snapshot": snapshot,
            "outcome": {
                "result": decision.outcome_result,
                "exit_price": float(decision.outcome_exit_price) if decision.outcome_exit_price is not None else None,
                "return_pct": float(decision.outcome_return_pct) if decision.outcome_return_pct is not None else None,
                "measured_at": (
                    decision.outcome_measured_at.isoformat() if decision.outcome_measured_at else None
                ),
            },
        },
    }
