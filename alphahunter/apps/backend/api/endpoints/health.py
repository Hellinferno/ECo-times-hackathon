"""Health endpoint — single GET that returns system liveness and feed status.

Returns:
  status / database       Always "healthy" / "connected" when the server responds.
  latest_scan / active_scan  Serialized ScanRun rows (latest overall + currently running).
  data_feeds              Quick ok/missing status for yfinance and tinyfish.
  tinyfish                Full WebIntelService health snapshot (provider, freshness per source).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy import desc
from sqlalchemy.orm import Session

from api.presenters import serialize_scan_run
from database import get_db
from models.db import ScanRun
from services.web_intel_service import WebIntelService

router = APIRouter()


@router.get("/")
def get_health(db: Session = Depends(get_db)):
    latest_scan = db.query(ScanRun).order_by(desc(ScanRun.started_at)).first()
    active_scan = db.query(ScanRun).filter(ScanRun.status == "running").order_by(desc(ScanRun.started_at)).first()

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
            "version": "1.1.0",
            "latest_scan": serialize_scan_run(latest_scan),
            "active_scan": serialize_scan_run(active_scan),
            "data_feeds": {
                "yfinance": "ok",
                "tinyfish": web_health.get("last_prefetch_status", "missing"),
            },
            "tinyfish": web_health,
        },
    }
