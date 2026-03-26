from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models.db import WatchlistItem, Stock, Decision
import datetime

router = APIRouter()

USER_ID = "default"


@router.get("")
def get_watchlist(db: Session = Depends(get_db)):
    """List all watchlist items with latest decision data."""
    items = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == USER_ID)
        .order_by(desc(WatchlistItem.added_at))
        .all()
    )

    payload = []
    for item in items:
        # Get latest decision for this symbol
        decision = (
            db.query(Decision)
            .filter(Decision.symbol == item.symbol)
            .order_by(desc(Decision.decided_at))
            .first()
        )

        entry = {
            "id": item.id,
            "symbol": item.symbol,
            "added_at": item.added_at.isoformat(),
            "notes": item.notes,
            "latest_action": decision.action if decision else None,
            "latest_confidence": float(decision.confidence) if decision else None,
            "latest_decided_at": decision.decided_at.isoformat() if decision else None,
        }
        payload.append(entry)

    return {"success": True, "data": payload}


@router.post("/{symbol}")
def add_to_watchlist(symbol: str, notes: str = None, db: Session = Depends(get_db)):
    """Add a stock to the watchlist."""
    symbol = symbol.upper()

    # Verify stock exists
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found in universe")

    # Check for duplicates
    existing = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == USER_ID, WatchlistItem.symbol == symbol)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"{symbol} is already in your watchlist")

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
        }
    }


@router.delete("/{symbol}")
def remove_from_watchlist(symbol: str, db: Session = Depends(get_db)):
    """Remove a stock from the watchlist."""
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
