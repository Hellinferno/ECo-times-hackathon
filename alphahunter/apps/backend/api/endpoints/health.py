from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session
from loguru import logger

from database import get_db
from models.db import ScanRun
from services.web_intel_service import WebIntelService

router = APIRouter()


@router.get("/")
def get_health(db: Session = Depends(get_db)):
    latest_scan = db.query(ScanRun).order_by(desc(ScanRun.started_at)).first()
    try:
        web_health = WebIntelService(db).get_health_snapshot()
    except Exception as exc:
        logger.warning(f"Health snapshot failed for tinyfish data feed: {exc}")
        web_health = {
            "provider": "disabled",
            "last_prefetch_at": None,
            "last_prefetch_status": "missing",
            "source_status": {},
            "source_freshness_minutes": {},
        }

    return {
        "success": True,
        "data": {
            "status": "healthy",
            "database": "connected",
            "last_scan": latest_scan.completed_at.isoformat() if latest_scan and latest_scan.completed_at else None,
            "data_feeds": {
                "yfinance": "ok",
                "tinyfish": web_health.get("last_prefetch_status", "missing"),
            },
            "tinyfish": web_health,
            "version": "1.1.0",
        },
    }
