"""Scan endpoint — trigger and monitor full pipeline execution runs.

Routes:
  POST  ""                    Trigger a new scan (errors if one is already running)
  GET   /latest               Serialized ScanRun for the most recent run
  GET   /{scan_run_id}/status  Status of a specific run by UUID

The synchronous execute_pipeline() function runs in a FastAPI BackgroundTask:
  DataAgent → SignalAgent → BacktestingAgent → ReasoningAgent → DecisionAgent → AuditAgent
In shadow mode an additional ShadowSignalDiff row is recorded per signal.
"""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger
from sqlalchemy import desc
from sqlalchemy.orm import Session

from agents import (
    AuditAgent,
    BacktestingAgent,
    DataAgent,
    DecisionAgent,
    ReasoningAgent,
    SignalAgent,
)
from api.presenters import serialize_scan_run
from database import SessionLocal, get_db
from models.db import Alert, ScanRun, Stock
from services.alert_service import get_alert_service
from utils.runtime_settings import get_runtime_settings, parse_float

router = APIRouter()

# Limit concurrent yfinance HTTP calls to avoid rate-limiting on the free tier
_YFINANCE_SEMAPHORE = threading.Semaphore(3)
_MAX_WORKERS = 10


# ── Per-symbol worker ─────────────────────────────────────────────────────────

def _process_symbol(
    symbol: str,
    scan_run_id: int,
    pipeline_mode: str,
    alert_confidence_threshold: float,
    signal_agent: SignalAgent,
    backtesting_agent: BacktestingAgent,
    reasoning_agent: ReasoningAgent,
    decision_agent: DecisionAgent,
) -> tuple[bool, bool]:
    """
    Run the full agent pipeline for one symbol in its own DB session.

    Returns (scanned: bool, signal_found: bool).
    Agents that are stateless (Signal/Backtest/Reasoning/Decision) are shared
    across threads — they hold no mutable state.  DataAgent and AuditAgent each
    get their own session so there are no cross-thread session conflicts.
    """
    db = SessionLocal()
    try:
        data_agent = DataAgent(db)
        audit_agent = AuditAgent(db)

        with _YFINANCE_SEMAPHORE:
            market_data = data_agent.get_market_data(symbol)
        if not market_data:
            return (True, False)

        bulk_deals = data_agent.get_bulk_deals(symbol, prefer_live=True)
        external_context = data_agent.get_external_context(symbol)

        signal_data = signal_agent.detect_signals(
            market_data,
            bulk_deals,
            external_context=external_context,
            mode=pipeline_mode,
        )
        signal_data["price"] = market_data["current_price"]
        signal_data["current_price"] = market_data["current_price"]
        signal_data["volume_today"] = market_data["volume_today"]
        signal_data["volume_avg_20d"] = signal_data.get("volume_spike_details", {}).get("avg_volume_20d")
        signal_data["volume_ratio"] = signal_data.get("volume_spike_details", {}).get("volume_ratio")

        if signal_data["signal_count"] == 0:
            return (True, False)

        with _YFINANCE_SEMAPHORE:
            hist_data = data_agent.get_historical_data_for_backtest(symbol)
        bt_results = backtesting_agent.evaluate_historical_signals(signal_data, hist_data)
        signal_data.update(bt_results)

        reasoning = reasoning_agent.generate_explanation(
            symbol,
            market_data["current_price"],
            signal_data,
            bt_results,
        )

        decision = decision_agent.evaluate(
            market_data["current_price"],
            signal_data["composite_score"],
            bt_results,
            signal_data,
        )

        if pipeline_mode == "shadow" and signal_data.get("grouped_composite_score") is not None:
            legacy_signal_details = dict(signal_data)
            legacy_signal_details["signal_count"] = sum([
                signal_data.get("breakout_triggered", False),
                signal_data.get("volume_spike_triggered", False),
                signal_data.get("bulk_deal_triggered", False),
            ])
            legacy_signal_details["max_signal_count"] = 3

            shadow_signal_details = dict(signal_data)
            shadow_signal_details["signal_count"] = sum([
                signal_data.get("breakout_triggered", False),
                signal_data.get("volume_spike_triggered", False),
                signal_data.get("bulk_deal_triggered", False),
                signal_data.get("news_sentiment_triggered", False),
                signal_data.get("social_sentiment_triggered", False),
                signal_data.get("insider_filing_triggered", False),
                signal_data.get("macro_context_triggered", False),
            ])
            shadow_signal_details["max_signal_count"] = 7

            legacy_decision = decision_agent.evaluate(
                market_data["current_price"],
                signal_data.get("legacy_composite_score", signal_data["composite_score"]),
                bt_results,
                legacy_signal_details,
            )
            shadow_decision = decision_agent.evaluate(
                market_data["current_price"],
                signal_data.get("grouped_composite_score", signal_data["composite_score"]),
                bt_results,
                shadow_signal_details,
            )
            audit_agent.log_shadow_diff(
                scan_run_id=scan_run_id,
                symbol=symbol,
                legacy_score=signal_data.get("legacy_composite_score", signal_data["composite_score"]),
                new_score=signal_data.get("grouped_composite_score", signal_data["composite_score"]),
                legacy_action=legacy_decision["action"],
                new_action=shadow_decision["action"],
                diff_payload={
                    "legacy_confidence": legacy_decision["confidence"],
                    "new_confidence": shadow_decision["confidence"],
                    "mode_effective": signal_data.get("signal_diagnostics", {}).get("mode_effective"),
                },
            )

        snapshot = {
            "market_data": {k: v for k, v in market_data.items() if k != "ohlcv_short"},
            "bulk_deals": bulk_deals,
            "external_context": external_context,
            "signals": signal_data,
            "backtest_results": bt_results,
            "reasoning": reasoning,
            "decision_metrics": decision,
        }

        result_id = audit_agent.log_scan_result(scan_run_id, signal_data, reasoning)
        if result_id:
            logged_decision = audit_agent.log_decision(result_id, symbol, decision, snapshot)

            if (
                decision.get("action") == "BUY"
                and float(decision.get("confidence", 0)) >= alert_confidence_threshold
            ):
                signal_labels = [
                    label for flag, label in [
                        (signal_data.get("breakout_triggered"), "Breakout"),
                        (signal_data.get("volume_spike_triggered"), "Volume Spike"),
                        (signal_data.get("bulk_deal_triggered"), "Bulk Deal"),
                    ] if flag
                ]
                signals_str = " + ".join(signal_labels) if signal_labels else "Multiple signals"
                msg = (
                    f"BUY signal on {symbol}: {signals_str} detected. "
                    f"Confidence: {decision.get('confidence', 0):.0f}%. "
                    f"Entry: ₹{decision.get('entry_price', 'N/A')}, "
                    f"Target: ₹{decision.get('target_price', 'N/A')}, "
                    f"Stop: ₹{decision.get('stop_loss', 'N/A')}."
                )
                alert = Alert(
                    symbol=symbol,
                    decision_id=logged_decision.decision_id if logged_decision else None,
                    alert_type="signal_triggered",
                    message=msg,
                    confidence=decision.get("confidence"),
                    action=decision.get("action"),
                    is_read=False,
                )
                db.add(alert)
                db.commit()

                # External delivery (Telegram, etc.) — fail-open
                get_alert_service().deliver_buy_alert(symbol, decision, signal_data)

        return (True, True)

    except Exception as exc:
        logger.error(f"Worker error for {symbol}: {exc}")
        db.rollback()
        return (True, False)
    finally:
        db.close()


# ── Pipeline orchestration ─────────────────────────────────────────────────────

def execute_pipeline(scan_run_id: int, symbols: list[str]):
    """
    Orchestrates parallel per-symbol pipeline execution.

    Uses a ThreadPoolExecutor with up to _MAX_WORKERS (10) concurrent workers.
    Each worker gets its own SQLAlchemy session — they must never share one.
    Stateless agents (SignalAgent, BacktestingAgent, etc.) are shared across
    threads to avoid repeated initialisation overhead.
    """
    db = SessionLocal()
    try:
        scan_run = db.query(ScanRun).get(scan_run_id)
        if not scan_run:
            return

        # Read pipeline settings once in the coordinator session
        runtime = get_runtime_settings(db)
        alert_confidence_threshold = parse_float(runtime, "default_alert_confidence_threshold", 65.0)

        # Prefetch external signals using the coordinator session/DataAgent
        coordinator_data_agent = DataAgent(db)
        pipeline_mode = coordinator_data_agent.get_pipeline_mode()
        prefetch_summary = coordinator_data_agent.ensure_external_signals_prefetched(
            symbols=symbols, force=False
        )
        logger.info(f"External signal prefetch: {prefetch_summary}")

        # Stateless agents — safe to share across threads
        signal_agent = SignalAgent()
        backtesting_agent = BacktestingAgent()
        reasoning_agent = ReasoningAgent()
        decision_agent = DecisionAgent()

        signals_found = 0
        stocks_scanned = 0

        with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
            futures = {
                executor.submit(
                    _process_symbol,
                    symbol,
                    scan_run_id,
                    pipeline_mode,
                    alert_confidence_threshold,
                    signal_agent,
                    backtesting_agent,
                    reasoning_agent,
                    decision_agent,
                ): symbol
                for symbol in symbols
            }
            for future in as_completed(futures):
                sym = futures[future]
                try:
                    scanned, signal_found = future.result()
                    if scanned:
                        stocks_scanned += 1
                    if signal_found:
                        signals_found += 1
                except Exception as exc:
                    logger.error(f"Future error for {sym}: {exc}")
                    stocks_scanned += 1  # count it as scanned even on error

        scan_run.status = "completed"
        scan_run.completed_at = datetime.utcnow()
        scan_run.stocks_scanned = stocks_scanned
        scan_run.signals_found = signals_found
        scan_run.duration_secs = (scan_run.completed_at - scan_run.started_at).total_seconds()
        db.commit()
        logger.info(
            f"Scan {scan_run_id} complete: {stocks_scanned} scanned, "
            f"{signals_found} signals, {scan_run.duration_secs:.1f}s"
        )
    except Exception as exc:
        logger.error(f"Pipeline coordinator crashed: {exc}")
        db.rollback()
        scan_run = db.query(ScanRun).get(scan_run_id)
        if scan_run:
            scan_run.status = "failed"
            scan_run.error_message = str(exc)
            scan_run.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("")
def trigger_scan(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger a full scan unless one is already in progress."""

    active_run = db.query(ScanRun).filter(ScanRun.status == "running").first()
    if active_run:
        raise HTTPException(status_code=409, detail="A scan is already running. Please wait.")

    run = ScanRun(triggered_by="manual", status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    stocks = db.query(Stock.symbol).filter(Stock.is_active.is_(True)).all()
    symbols = [row[0] for row in stocks]

    background_tasks.add_task(execute_pipeline, run.id, symbols)

    return {
        "success": True,
        "data": {
            "scan_run_id": str(run.run_id),
            "status": run.status,
            "started_at": run.started_at.isoformat(),
            "stocks_queued": len(symbols),
        },
    }


@router.get("/latest")
def get_latest_scan(db: Session = Depends(get_db)):
    latest = db.query(ScanRun).order_by(desc(ScanRun.started_at)).first()
    return {"success": True, "data": serialize_scan_run(latest)}


@router.get("/{scan_run_id}/status")
def get_scan_status(scan_run_id: str, db: Session = Depends(get_db)):
    try:
        parsed_scan_id = UUID(scan_run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid scan run id") from exc

    run = db.query(ScanRun).filter(ScanRun.run_id == parsed_scan_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Scan run not found")
    return {"success": True, "data": serialize_scan_run(run)}
