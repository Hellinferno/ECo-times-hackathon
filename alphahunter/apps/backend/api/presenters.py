"""Response serialisation helpers used across all API endpoints.

Sections
--------
- Type coercions       — safe float/int conversions that handle NaN/Infinity
- JSON helpers         — coerce/parse arbitrary JSON columns from ORM models
- Signal helpers       — build signal lists from ScanResult rows
- Scan run             — serialize ScanRun → API dict
- Opportunity          — serialize Decision+ScanResult+Stock → opportunity payload
- Decision history     — serialize Decision for history/audit trail endpoints
- Signals summary      — full signal breakdown for stock-detail / history views
- Backtest             — serialize backtest fields from ScanResult
"""
from __future__ import annotations

import json
import math
from typing import Any

from models.db import Decision, ScanResult, ScanRun, Stock
from utils.nan import sanitize_nan


# ── Type coercions ─────────────────────────────────────────────────────────────

def to_float(value: Any) -> float | None:
    """Convert value to float, returning None for null / NaN / Infinity."""
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result) or math.isinf(result):
        return None
    return result


def to_int(value: Any) -> int | None:
    """Convert value to int, returning None for null / unconvertible values."""
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# ── JSON helpers ───────────────────────────────────────────────────────────────

def coerce_json(value: Any, fallback: Any = None) -> Any:
    """Return a sanitised dict/list from a JSON column or raw Python value."""
    if fallback is None:
        fallback = {}
    if value is None:
        return fallback
    if isinstance(value, (dict, list)):
        return sanitize_nan(value)
    if isinstance(value, str):
        try:
            return sanitize_nan(json.loads(value))
        except json.JSONDecodeError:
            return fallback
    return fallback


def parse_reasoning(raw_reasoning: Any) -> dict[str, Any]:
    """Parse the reasoning_text column into a structured dict."""
    if raw_reasoning is None:
        return {}
    if isinstance(raw_reasoning, dict):
        return raw_reasoning
    if isinstance(raw_reasoning, str):
        try:
            parsed = json.loads(raw_reasoning)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {"llm_summary": raw_reasoning}
    return {}


# ── Signal helpers ─────────────────────────────────────────────────────────────

def build_signal_list(scan_result: ScanResult | None) -> list[str]:
    """Return a list of triggered signal keys for a given ScanResult."""
    if not scan_result:
        return []

    signals: list[str] = []
    if scan_result.breakout_triggered:
        signals.append("breakout")
    if scan_result.volume_spike_triggered:
        signals.append("volume_spike")
    if scan_result.bulk_deal_triggered:
        signals.append("bulk_deal")

    # Extended TinyFish-derived signals stored in extra_signals_json
    extras = coerce_json(scan_result.extra_signals_json)
    for extra_key in ("news_sentiment", "social_sentiment", "insider_filing", "macro_context"):
        if extras.get(extra_key, {}).get("triggered"):
            signals.append(extra_key)

    return signals


# ── Scan run ───────────────────────────────────────────────────────────────────

def serialize_scan_run(run: ScanRun | None) -> dict[str, Any] | None:
    if not run:
        return None
    return {
        "id": run.id,
        "scan_run_id": str(run.run_id),
        "triggered_by": run.triggered_by,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "duration_secs": to_float(run.duration_secs),
        "stocks_scanned": run.stocks_scanned or 0,
        "signals_found": run.signals_found or 0,
        "error_message": run.error_message,
    }


# ── Opportunity ────────────────────────────────────────────────────────────────

def serialize_opportunity(
    decision: Decision,
    scan_result: ScanResult | None,
    stock: Stock | None = None,
) -> dict[str, Any]:
    """Flatten Decision + ScanResult + Stock into the opportunity API shape."""
    reasoning = parse_reasoning(scan_result.reasoning_text if scan_result else None)
    signals = build_signal_list(scan_result)
    return {
        "decision_id": str(decision.decision_id),
        "symbol": decision.symbol,
        "name": stock.name if stock else decision.symbol,
        "sector": stock.sector if stock else None,
        "action": decision.action,
        "confidence": to_float(decision.confidence) or 0.0,
        "entry_price": to_float(decision.entry_price),
        "target_price": to_float(decision.target_price),
        "stop_loss": to_float(decision.stop_loss),
        "rr_ratio": to_float(decision.rr_ratio),
        "price": to_float(scan_result.price) if scan_result else None,
        "signal_count": scan_result.signal_count if scan_result else 0,
        "signals": signals,
        "composite_score": to_float(scan_result.composite_score) if scan_result else None,
        "reasoning": reasoning,
        "scanned_at": scan_result.scanned_at.isoformat() if scan_result and scan_result.scanned_at else None,
        "decided_at": decision.decided_at.isoformat() if decision.decided_at else None,
    }


# ── Decision history ───────────────────────────────────────────────────────────

def serialize_decision_entry(decision: Decision, stock: Stock | None = None) -> dict[str, Any]:
    """Serialize a Decision for history / audit trail endpoints."""
    return {
        "decision_id": str(decision.decision_id),
        "symbol": decision.symbol,
        "name": stock.name if stock else decision.symbol,
        "sector": stock.sector if stock else None,
        "action": decision.action,
        "confidence": to_float(decision.confidence) or 0.0,
        "entry_price": to_float(decision.entry_price),
        "target_price": to_float(decision.target_price),
        "stop_loss": to_float(decision.stop_loss),
        "rr_ratio": to_float(decision.rr_ratio),
        "decided_at": decision.decided_at.isoformat() if decision.decided_at else None,
        "outcome_measured": bool(decision.outcome_measured),
        "outcome_return_pct": to_float(decision.outcome_return_pct),
        "outcome_result": decision.outcome_result,
        "outcome_exit_price": to_float(decision.outcome_exit_price),
        "outcome_measured_at": (
            decision.outcome_measured_at.isoformat() if decision.outcome_measured_at else None
        ),
    }


# ── Signals summary ────────────────────────────────────────────────────────────

def summarize_signals(scan_result: ScanResult | None) -> dict[str, Any] | None:
    """Return the full signal breakdown used by stock-detail and history endpoints."""
    if not scan_result:
        return None

    breakout_details = coerce_json(scan_result.breakout_details)
    volume_details = coerce_json(scan_result.volume_spike_details)
    bulk_details = coerce_json(scan_result.bulk_deal_details)

    return {
        "signal_count": scan_result.signal_count,
        "composite_score": to_float(scan_result.composite_score),
        "price": to_float(scan_result.price),
        "volume_today": to_int(scan_result.volume_today),
        "volume_avg_20d": to_int(scan_result.volume_avg_20d),
        "volume_ratio": to_float(scan_result.volume_ratio),
        "items": [
            {
                "key": "breakout",
                "label": "Breakout",
                "triggered": bool(scan_result.breakout_triggered),
                "strength": to_float(breakout_details.get("strength")),
                "details": breakout_details,
            },
            {
                "key": "volume_spike",
                "label": "Volume Spike",
                "triggered": bool(scan_result.volume_spike_triggered),
                "strength": to_float(
                    volume_details.get("strength") or volume_details.get("volume_ratio")
                ),
                "details": volume_details,
            },
            {
                "key": "bulk_deal",
                "label": "Bulk Deal",
                "triggered": bool(scan_result.bulk_deal_triggered),
                "strength": to_float(bulk_details.get("strength")),
                "details": bulk_details,
            },
        ],
        "diagnostics": coerce_json(scan_result.data_quality_json),
        "extra_signals": coerce_json(scan_result.extra_signals_json),
    }


# ── Backtest ───────────────────────────────────────────────────────────────────

def serialize_backtest(scan_result: ScanResult | None) -> dict[str, Any] | None:
    if not scan_result:
        return None
    return {
        "matches": scan_result.backtest_matches,
        "success_rate": to_float(scan_result.backtest_success_rate),
        "avg_return_pct": to_float(scan_result.backtest_avg_return),
        "worst_case_pct": to_float(scan_result.backtest_worst_case),
        "best_case_pct": to_float(scan_result.backtest_best_case),
        "cases": coerce_json(scan_result.backtest_cases_json, fallback=[]),
    }
