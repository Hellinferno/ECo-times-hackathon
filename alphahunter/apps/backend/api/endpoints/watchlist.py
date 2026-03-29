"""Watchlist endpoint — single-user tracked symbols list.

Routes:
  GET     ""           List watchlist items with latest decision and signal summary
  POST    /{symbol}    Add a stock (enforces MAX_WATCHLIST_ITEMS=20 cap per user)
  DELETE  /{symbol}    Remove a stock from the watchlist

MVP uses a hard-coded USER_ID="default". Replace with auth-derived user_id
when multi-user support is added.
"""
from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import get_db
from models.db import Decision, ScanResult, Stock, WatchlistItem

router = APIRouter()

# Single-user mode: all watchlist items are owned by this hard-coded ID.
# Replace with auth-derived user_id when multi-user support is added.
USER_ID = "default"
MAX_WATCHLIST_ITEMS = 20


@router.get("")
def get_watchlist(db: Session = Depends(get_db)):
    """List all watchlist items with latest decision and signal context."""

    items = (
        db.query(WatchlistItem, Stock)
        .join(Stock, Stock.symbol == WatchlistItem.symbol)
        .filter(WatchlistItem.user_id == USER_ID)
        .order_by(desc(WatchlistItem.added_at))
        .all()
    )

    payload = []
    for item, stock in items:
        decision = (
            db.query(Decision)
            .filter(Decision.symbol == item.symbol)
            .order_by(desc(Decision.decided_at))
            .first()
        )
        scan_result = None
        if decision and decision.scan_result_id:
            scan_result = db.query(ScanResult).filter(ScanResult.id == decision.scan_result_id).first()

        payload.append(
            {
                "id": item.id,
                "symbol": item.symbol,
                "name": stock.name,
                "sector": stock.sector,
                "added_at": item.added_at.isoformat(),
                "notes": item.notes,
                "latest_action": decision.action if decision else None,
                "latest_confidence": float(decision.confidence) if decision and decision.confidence is not None else None,
                "latest_decided_at": decision.decided_at.isoformat() if decision and decision.decided_at else None,
                "latest_signal_count": scan_result.signal_count if scan_result else 0,
                "last_scanned_at": scan_result.scanned_at.isoformat() if scan_result and scan_result.scanned_at else None,
                "has_active_signal": bool(scan_result and scan_result.signal_count),
            }
        )

    return {"success": True, "data": {"count": len(payload), "items": payload, "max_items": MAX_WATCHLIST_ITEMS}}


@router.post("/{symbol}")
def add_to_watchlist(symbol: str, notes: str | None = None, db: Session = Depends(get_db)):
    """Add a stock to the watchlist, enforcing the single-user cap."""

    symbol = symbol.upper()

    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found in universe")

    existing = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == USER_ID, WatchlistItem.symbol == symbol)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"{symbol} is already in your watchlist")

    current_count = db.query(WatchlistItem).filter(WatchlistItem.user_id == USER_ID).count()
    if current_count >= MAX_WATCHLIST_ITEMS:
        raise HTTPException(
            status_code=409,
            detail=f"Watchlist limit reached. You can track up to {MAX_WATCHLIST_ITEMS} stocks.",
        )

    item = WatchlistItem(
        user_id=USER_ID,
        symbol=symbol,
        notes=notes,
        added_at=datetime.datetime.utcnow(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return {
        "success": True,
        "data": {
            "id": item.id,
            "symbol": item.symbol,
            "added_at": item.added_at.isoformat(),
            "notes": item.notes,
            "max_items": MAX_WATCHLIST_ITEMS,
        },
    }


@router.delete("/{symbol}")
def remove_from_watchlist(symbol: str, db: Session = Depends(get_db)):
    symbol = symbol.upper()
    item = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == USER_ID, WatchlistItem.symbol == symbol)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail=f"{symbol} not found in watchlist")

    db.delete(item)
    db.commit()

    return {"success": True, "data": {"symbol": symbol, "removed": True}}
