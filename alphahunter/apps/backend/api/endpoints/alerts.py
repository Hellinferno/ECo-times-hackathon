"""Alerts endpoint — list, mark-read, and clear in-app notifications.

Routes:
  GET    ""           List alerts (optionally unread-only) + unread count
  POST   /mark-read   Bulk mark selected (or all unread) alerts as read
  DELETE /read        Purge all already-read alerts
"""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import get_db
from models.db import Alert

router = APIRouter()


@router.get("")
def list_alerts(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """List alerts together with the current unread count."""

    unread_count = db.query(Alert).filter(Alert.is_read.is_(False)).count()

    query = db.query(Alert)
    if unread_only:
        query = query.filter(Alert.is_read.is_(False))

    alerts = query.order_by(desc(Alert.created_at)).limit(limit).all()

    payload = [
        {
            "id": alert.id,
            "alert_id": str(alert.alert_id),
            "symbol": alert.symbol,
            "alert_type": alert.alert_type,
            "message": alert.message,
            "confidence": float(alert.confidence) if alert.confidence is not None else None,
            "action": alert.action,
            "is_read": alert.is_read,
            "created_at": alert.created_at.isoformat(),
        }
        for alert in alerts
    ]

    return {"success": True, "data": {"unread_count": unread_count, "alerts": payload}}


@router.post("/mark-read")
def mark_alerts_read(alert_ids: list[int] | None = Body(default=None), db: Session = Depends(get_db)):
    """Mark selected alerts as read. If no ids are passed, mark all unread alerts."""

    query = db.query(Alert).filter(Alert.is_read.is_(False))
    if alert_ids:
        query = query.filter(Alert.id.in_(alert_ids))

    updated = query.update({"is_read": True}, synchronize_session="fetch")
    db.commit()

    return {"success": True, "data": {"marked_read": updated}}


@router.delete("/read")
def clear_read_alerts(db: Session = Depends(get_db)):
    """Delete all alerts that have already been marked as read."""

    cleared = db.query(Alert).filter(Alert.is_read.is_(True)).delete(synchronize_session="fetch")
    db.commit()
    return {"success": True, "data": {"cleared": cleared}}
