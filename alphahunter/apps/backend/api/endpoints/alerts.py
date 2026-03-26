from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models.db import Alert

router = APIRouter()


@router.get("")
def list_alerts(
    unread_only: bool = Query(False),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """List alerts, optionally filtered to unread only."""
    query = db.query(Alert)
    if unread_only:
        query = query.filter(Alert.is_read == False)
    alerts = query.order_by(desc(Alert.created_at)).limit(limit).all()

    payload = []
    for a in alerts:
        payload.append({
            "id": a.id,
            "alert_id": str(a.alert_id),
            "symbol": a.symbol,
            "alert_type": a.alert_type,
            "message": a.message,
            "confidence": float(a.confidence) if a.confidence else None,
            "action": a.action,
            "is_read": a.is_read,
            "created_at": a.created_at.isoformat(),
        })

    return {"success": True, "data": payload}


@router.post("/mark-read")
def mark_alerts_read(alert_ids: list[int] = None, db: Session = Depends(get_db)):
    """Mark alerts as read. If alert_ids is empty/null, marks all as read."""
    query = db.query(Alert).filter(Alert.is_read == False)
    if alert_ids:
        query = query.filter(Alert.id.in_(alert_ids))

    updated = query.update({"is_read": True}, synchronize_session="fetch")
    db.commit()

    return {"success": True, "data": {"marked_read": updated}}
