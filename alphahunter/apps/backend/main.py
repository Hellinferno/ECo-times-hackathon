"""AlphaHunter Intelligence Platform — FastAPI application entry point.

Startup sequence
----------------
1. ``Base.metadata.create_all`` ensures all ORM tables exist (dev convenience;
   Alembic is the long-term migration path).
2. ``BackgroundScheduler`` begins a 5-minute TinyFish prefetch cycle.

NaN sanitisation
----------------
yfinance can produce NaN/Infinity floats for missing OHLCV fields.  Standard
``json.dumps`` emits bare ``NaN`` / ``Infinity`` which is not valid JSON.
``NanSafeJSONResponse`` replaces those values with ``null`` at serialisation
time — no middleware needed, so there are no Content-Length header mismatches.
"""
from __future__ import annotations

import json
import threading
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from agents import DataAgent
from api.router import api_router
from utils.nan import sanitize_nan
from config import settings
from database import SessionLocal, engine
from models.db import Base, ScanRun, Stock

_IST = ZoneInfo("Asia/Kolkata")


# ── NaN / Infinity safe JSON response ─────────────────────────────────────────

class NanSafeJSONResponse(JSONResponse):
    """JSONResponse subclass that replaces NaN/Infinity with null before encoding."""

    def render(self, content) -> bytes:
        return json.dumps(
            sanitize_nan(content),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")


# ── WebSocket connection manager ───────────────────────────────────────────────

class ScanStatusManager:
    """
    Manages active WebSocket connections for real-time scan progress updates.

    Call broadcast_scan_status() from anywhere to push a JSON payload to all
    connected clients (e.g. from the scan pipeline as stocks complete).
    Thread-safe: uses an asyncio-safe approach with a message queue.
    """

    def __init__(self):
        self.active: list[WebSocket] = []
        self._lock = threading.Lock()

    def connect(self, ws: WebSocket) -> None:
        with self._lock:
            self.active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        with self._lock:
            try:
                self.active.remove(ws)
            except ValueError:
                pass

    async def broadcast(self, payload: dict) -> None:
        import asyncio
        import json as _json
        message = _json.dumps(payload)
        dead: list[WebSocket] = []
        with self._lock:
            connections = list(self.active)
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


ws_manager = ScanStatusManager()


# ── Background scheduler ───────────────────────────────────────────────────────

scheduler = BackgroundScheduler()


def _prefetch_external_job():
    """Scheduled job: keep TinyFish signal cache warm for all active stocks."""
    db = SessionLocal()
    try:
        symbols = [row[0] for row in db.query(Stock.symbol).filter(Stock.is_active.is_(True)).all()]
        if not symbols:
            return
        result = DataAgent(db).ensure_external_signals_prefetched(symbols=symbols, force=False)
        logger.info(f"Scheduled TinyFish prefetch result: {result}")
    except Exception as exc:
        logger.error(f"Scheduled TinyFish prefetch failed: {exc}")
    finally:
        db.close()


def _market_scan_job():
    """
    Scheduled job: trigger an automated market scan during NSE trading hours.

    Runs every 15 minutes Mon–Fri, 09:15–15:30 IST.
    Skips if a scan is already in progress.
    The pipeline runs in a daemon thread so the scheduler thread is not blocked.
    """
    # Late import avoids a circular import at module load time
    from api.endpoints.scan import execute_pipeline  # noqa: PLC0415

    db = SessionLocal()
    try:
        active_run = db.query(ScanRun).filter(ScanRun.status == "running").first()
        if active_run:
            logger.debug("Scheduled scan skipped — a scan is already running.")
            return

        symbols = [row[0] for row in db.query(Stock.symbol).filter(Stock.is_active.is_(True)).all()]
        if not symbols:
            logger.warning("Scheduled scan skipped — no active stocks found.")
            return

        run = ScanRun(triggered_by="scheduler", status="running")
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id

        logger.info(f"Scheduled market scan started: run_id={run_id}, {len(symbols)} symbols")
        t = threading.Thread(target=execute_pipeline, args=(run_id, symbols), daemon=True)
        t.start()
    except Exception as exc:
        logger.error(f"Scheduled market scan failed to start: {exc}")
        db.rollback()
    finally:
        db.close()


# ── Application lifespan ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    Base.metadata.create_all(bind=engine)
    if not scheduler.running:
        # Keep TinyFish signal cache warm every 5 minutes
        scheduler.add_job(
            _prefetch_external_job,
            "interval",
            minutes=5,
            id="tinyfish_prefetch",
            replace_existing=True,
        )
        # Automated market scan every 15 minutes during NSE trading hours (Mon–Fri, 09:15–15:30 IST)
        scheduler.add_job(
            _market_scan_job,
            "cron",
            day_of_week="mon-fri",
            hour="9-15",
            minute="15,30,45,0",  # :00, :15, :30, :45 within the hour window
            timezone=_IST,
            id="market_hours_scan",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Background scheduler started: TinyFish prefetch (5 min) + market scan (15 min, IST hours)")
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


# ── FastAPI application ────────────────────────────────────────────────────────

app = FastAPI(
    title="AlphaHunter Intelligence Platform",
    description="Unified market intelligence, research workspace, and valuation platform.",
    version="2.0.0",
    lifespan=lifespan,
    default_response_class=NanSafeJSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_allowed_origins,
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.websocket("/ws/scan-status")
async def websocket_scan_status(websocket: WebSocket):
    """
    WebSocket endpoint for real-time scan progress.

    Clients connect here and receive JSON messages as scans progress:
      {"type": "scan_started",  "scan_run_id": "...", "stocks_queued": N}
      {"type": "scan_progress", "scan_run_id": "...", "stocks_scanned": N, "signals_found": M}
      {"type": "scan_complete", "scan_run_id": "...", "duration_secs": X}
      {"type": "scan_failed",   "scan_run_id": "...", "error": "..."}
    """
    await websocket.accept()
    ws_manager.connect(websocket)
    try:
        # Send current scan status on connect
        db = SessionLocal()
        try:
            from sqlalchemy import desc as _desc
            latest = db.query(ScanRun).order_by(_desc(ScanRun.started_at)).first()
            if latest:
                await websocket.send_text(
                    __import__("json").dumps({
                        "type": "connected",
                        "latest_scan": {
                            "scan_run_id": str(latest.run_id),
                            "status": latest.status,
                            "stocks_scanned": latest.stocks_scanned or 0,
                            "signals_found": latest.signals_found or 0,
                        }
                    })
                )
        finally:
            db.close()

        # Keep connection alive — client messages are ignored (read-only channel)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)
