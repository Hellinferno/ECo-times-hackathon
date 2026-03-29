"""Stock endpoint — per-symbol chart data and full analysis detail.

Routes:
  GET  /{symbol}/chart  OHLCV bars + backtest signal markers + reference price levels
                        period: 1mo | 3mo | 6mo | 1y | 2y
                        interval: 1d | 1wk
  GET  /{symbol}        Latest decision, signal summary, reasoning, and backtest stats
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from agents import DataAgent
from api.presenters import coerce_json, parse_reasoning, serialize_backtest, summarize_signals, to_float
from database import get_db
from models.db import Decision, ScanResult, Stock
from utils.runtime_settings import get_runtime_settings

router = APIRouter()


@router.get("/{symbol}/chart")
def get_stock_chart(
    symbol: str,
    period: str = Query(default="6mo"),
    interval: str = Query(default="1d"),
    db: Session = Depends(get_db),
):
    """Return OHLCV chart data plus signal markers and reference levels."""

    allowed_periods = {"1mo", "3mo", "6mo", "1y", "2y"}
    allowed_intervals = {"1d", "1wk"}
    if period not in allowed_periods:
        raise HTTPException(status_code=400, detail="Unsupported chart period")
    if interval not in allowed_intervals:
        raise HTTPException(status_code=400, detail="Unsupported chart interval")

    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    decision = (
        db.query(Decision)
        .filter(Decision.symbol == symbol.upper())
        .order_by(desc(Decision.decided_at))
        .first()
    )
    scan_result = None
    if decision and decision.scan_result_id:
        scan_result = db.query(ScanResult).filter(ScanResult.id == decision.scan_result_id).first()

    chart_data = DataAgent(db).get_chart_data(symbol.upper(), period=period, interval=interval)
    markers = []
    cases = scan_result.backtest_cases_json if scan_result and scan_result.backtest_cases_json else []
    if isinstance(cases, list):
        for case in cases:
            case_date = case.get("date")
            if not case_date:
                continue
            markers.append(
                {
                    "date": case_date,
                    "type": "backtest_case",
                    "return_pct": to_float(case.get("return_pct")),
                    "profitable": (to_float(case.get("return_pct")) or 0) >= 0,
                }
            )

    breakout_details = coerce_json(scan_result.breakout_details if scan_result else None)

    reference_levels = {
        "resistance_level": to_float((breakout_details or {}).get("resistance_level")),
        "support_level": to_float(decision.stop_loss) if decision and decision.stop_loss is not None else None,
        "target_price": to_float(decision.target_price) if decision and decision.target_price is not None else None,
    }

    return {
        "success": True,
        "data": {
            "symbol": stock.symbol,
            "period": period,
            "interval": interval,
            "ohlcv": chart_data,
            "signal_markers": markers,
            **reference_levels,
        },
    }


@router.get("/{symbol}")
def get_stock_detail(symbol: str, db: Session = Depends(get_db)):
    """Return full detail for the latest analysis of a stock."""

    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    settings = get_runtime_settings(db)
    decision = (
        db.query(Decision)
        .filter(Decision.symbol == symbol.upper())
        .order_by(desc(Decision.decided_at))
        .first()
    )

    scan_result = None
    if decision and decision.scan_result_id:
        scan_result = db.query(ScanResult).filter(ScanResult.id == decision.scan_result_id).first()

    stock_data = {
        "symbol": stock.symbol,
        "name": stock.name,
        "sector": stock.sector,
        "market_cap_cr": to_float(stock.market_cap_cr),
        "is_active": stock.is_active,
    }

    if not decision:
        return {
            "success": True,
            "data": {
                "stock": stock_data,
                "meta": None,
                "decision": None,
                "signals": None,
                "reasoning": None,
                "backtest": None,
            },
        }

    decision_data = {
        "decision_id": str(decision.decision_id),
        "action": decision.action,
        "confidence": to_float(decision.confidence) or 0.0,
        "entry_price": to_float(decision.entry_price),
        "target_price": to_float(decision.target_price),
        "stop_loss": to_float(decision.stop_loss),
        "rr_ratio": to_float(decision.rr_ratio),
        "score_breakdown": {
            "signal_score": to_float(decision.score_signal),
            "backtest_score": to_float(decision.score_backtest),
            "composite_score": to_float(decision.score_composite),
        },
        "decided_at": decision.decided_at.isoformat(),
        "outcome_measured": decision.outcome_measured,
        "outcome_return_pct": to_float(decision.outcome_return_pct),
        "outcome_result": decision.outcome_result,
    }

    return {
        "success": True,
        "data": {
            "stock": stock_data,
            "meta": {
                "scanned_at": scan_result.scanned_at.isoformat() if scan_result and scan_result.scanned_at else None,
                "backtest_lookback_years": settings.get("backtest_lookback_years", "2"),
                "backtest_outcome_days": settings.get("backtest_outcome_days", "5"),
            },
            "decision": decision_data,
            "signals": summarize_signals(scan_result),
            "reasoning": parse_reasoning(scan_result.reasoning_text if scan_result else None),
            "backtest": serialize_backtest(scan_result),
        },
    }
