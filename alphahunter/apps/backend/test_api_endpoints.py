"""Integration tests for the AlphaHunter API.

Uses an in-memory SQLite database (StaticPool) wired into FastAPI via
dependency override — no running postgres or redis required.

Test coverage:
  - test_opportunities_filters_and_scan_status  GET /opportunities + /scan
  - test_history_detail_and_export              GET /history + /history/export
  - test_stock_chart_alerts_health_and_watchlist_cap
                                                GET /stock /alerts /health + POST /watchlist cap
"""
from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from agents.data_agent import DataAgent
from api.router import api_router
from database import get_db
from models.db import Alert, Base, Decision, ScanResult, ScanRun, Stock, WatchlistItem


# ── Test setup ─────────────────────────────────────────────────────────────────

def build_test_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(api_router, prefix="/api")

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), SessionLocal


def seed_reference_data(db):
    """Populate the in-memory DB with 3 scan runs, 3 stocks, 2 scan results,
    2 decisions, 2 alerts, and 1 watchlist item for use across all tests."""
    now = datetime.utcnow()
    older_run = ScanRun(
        run_id=uuid.uuid4(),
        triggered_by="scheduler",
        status="completed",
        started_at=now - timedelta(hours=2),
        completed_at=now - timedelta(hours=2, minutes=-1),
        stocks_scanned=2,
        signals_found=1,
        duration_secs=55,
    )
    latest_run = ScanRun(
        run_id=uuid.uuid4(),
        triggered_by="manual",
        status="completed",
        started_at=now - timedelta(minutes=10),
        completed_at=now - timedelta(minutes=9),
        stocks_scanned=3,
        signals_found=2,
        duration_secs=48,
    )
    running_run = ScanRun(
        run_id=uuid.uuid4(),
        triggered_by="manual",
        status="running",
        started_at=now - timedelta(minutes=1),
        stocks_scanned=0,
        signals_found=0,
    )

    stocks = [
        Stock(symbol="INFY", name="Infosys Ltd", sector="Technology"),
        Stock(symbol="TCS", name="Tata Consultancy Services", sector="Technology"),
        Stock(symbol="RELIANCE", name="Reliance Industries", sector="Energy"),
    ]

    db.add_all([older_run, latest_run, running_run, *stocks])
    db.commit()
    db.refresh(older_run)
    db.refresh(latest_run)
    db.refresh(running_run)

    infy_result = ScanResult(
        scan_run_id=latest_run.id,
        symbol="INFY",
        scanned_at=latest_run.completed_at,
        price=1502.45,
        volume_today=4600000,
        volume_avg_20d=2000000,
        volume_ratio=2.3,
        breakout_triggered=True,
        volume_spike_triggered=True,
        bulk_deal_triggered=False,
        breakout_details={"resistance_level": 1500, "pct_above": 0.16, "strength": 0.82},
        volume_spike_details={"volume_ratio": 2.3, "strength": 0.77},
        bulk_deal_details={},
        extra_signals_json={"news_sentiment": {"triggered": True}},
        data_quality_json={"fresh": True},
        signal_count=2,
        composite_score=0.82,
        reasoning_text='{"llm_summary":"INFY broke resistance on strong volume.","key_factors":["Breakout confirmed","Volume is 2.3x average"]}',
        backtest_matches=5,
        backtest_success_rate=80,
        backtest_avg_return=5.2,
        backtest_worst_case=-3.1,
        backtest_best_case=9.8,
        backtest_cases_json=[
            {"date": "2026-02-10", "entry_price": 1440, "exit_price": 1510, "return_pct": 4.8},
            {"date": "2025-11-10", "entry_price": 1380, "exit_price": 1460, "return_pct": 5.8},
        ],
    )
    tcs_result = ScanResult(
        scan_run_id=latest_run.id,
        symbol="TCS",
        scanned_at=latest_run.completed_at,
        price=4100,
        volume_today=1200000,
        volume_avg_20d=1100000,
        volume_ratio=1.1,
        breakout_triggered=False,
        volume_spike_triggered=False,
        bulk_deal_triggered=True,
        breakout_details={},
        volume_spike_details={},
        bulk_deal_details={"client_name": "Axis Mutual Fund", "price": 4065, "strength": 0.65},
        extra_signals_json={},
        data_quality_json={"fresh": True},
        signal_count=1,
        composite_score=0.56,
        reasoning_text='{"llm_summary":"TCS is supported by fresh institutional flow."}',
        backtest_matches=2,
        backtest_success_rate=50,
        backtest_avg_return=1.5,
        backtest_worst_case=-2.0,
        backtest_best_case=5.0,
        backtest_cases_json=[{"date": "2025-12-01", "entry_price": 3950, "exit_price": 4010, "return_pct": 1.5}],
    )

    db.add_all([infy_result, tcs_result])
    db.commit()
    db.refresh(infy_result)
    db.refresh(tcs_result)

    infy_decision = Decision(
        decision_id=uuid.uuid4(),
        scan_result_id=infy_result.id,
        symbol="INFY",
        decided_at=latest_run.completed_at,
        action="BUY",
        confidence=78,
        entry_price=1502.45,
        target_price=1580,
        stop_loss=1455,
        rr_ratio=2.3,
        score_signal=0.82,
        score_backtest=0.8,
        score_composite=0.78,
        snapshot_json={"decision_metrics": {"confidence": 78}},
        outcome_measured=True,
        outcome_exit_price=1551,
        outcome_return_pct=4.8,
        outcome_result="WIN",
        outcome_measured_at=latest_run.completed_at + timedelta(days=5),
    )
    tcs_decision = Decision(
        decision_id=uuid.uuid4(),
        scan_result_id=tcs_result.id,
        symbol="TCS",
        decided_at=latest_run.completed_at,
        action="WATCH",
        confidence=58,
        entry_price=4100,
        target_price=4210,
        stop_loss=4010,
        rr_ratio=1.2,
        score_signal=0.56,
        score_backtest=0.5,
        score_composite=0.58,
        snapshot_json={"decision_metrics": {"confidence": 58}},
        outcome_measured=False,
    )

    db.add_all([infy_decision, tcs_decision])
    db.add_all(
        [
            Alert(
                alert_id=uuid.uuid4(),
                symbol="INFY",
                decision_id=infy_decision.decision_id,
                alert_type="signal_triggered",
                message="INFY triggered a BUY signal",
                confidence=78,
                action="BUY",
                is_read=False,
                created_at=latest_run.completed_at,
            ),
            Alert(
                alert_id=uuid.uuid4(),
                symbol="TCS",
                decision_id=tcs_decision.decision_id,
                alert_type="signal_triggered",
                message="TCS triggered a WATCH signal",
                confidence=58,
                action="WATCH",
                is_read=True,
                created_at=latest_run.completed_at,
            ),
        ]
    )
    db.add(WatchlistItem(user_id="default", symbol="INFY", added_at=latest_run.completed_at))
    db.commit()

    return {
        "latest_run": latest_run,
        "running_run": running_run,
        "infy_decision": infy_decision,
        "tcs_decision": tcs_decision,
    }


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_opportunities_filters_and_scan_status():
    client, SessionLocal = build_test_client()
    db = SessionLocal()
    try:
        seeded = seed_reference_data(db)

        opportunities = client.get("/api/opportunities")
        assert opportunities.status_code == 200
        payload = opportunities.json()["data"]
        assert payload["scan_run_id"] == str(seeded["latest_run"].run_id)
        assert payload["total"] == 2
        assert payload["opportunities"][0]["symbol"] == "INFY"

        filtered = client.get("/api/opportunities", params={"action": "BUY"})
        assert filtered.status_code == 200
        assert filtered.json()["data"]["total"] == 1

        signal_filtered = client.get("/api/opportunities", params={"signal": "bulk_deal"})
        assert signal_filtered.status_code == 200
        assert signal_filtered.json()["data"]["opportunities"][0]["symbol"] == "TCS"

        latest_scan = client.get("/api/scan/latest")
        assert latest_scan.status_code == 200
        assert latest_scan.json()["data"]["status"] == "running"

        scan_status = client.get(f"/api/scan/{seeded['running_run'].run_id}/status")
        assert scan_status.status_code == 200
        assert scan_status.json()["data"]["scan_run_id"] == str(seeded["running_run"].run_id)
    finally:
        db.close()


def test_history_detail_and_export():
    client, SessionLocal = build_test_client()
    db = SessionLocal()
    try:
        seeded = seed_reference_data(db)

        history = client.get("/api/history", params={"symbol": "INFY", "outcome": "profit"})
        assert history.status_code == 200
        history_payload = history.json()["data"]
        assert history_payload["summary"]["total_decisions"] == 1
        assert history_payload["decisions"][0]["symbol"] == "INFY"

        detail = client.get(f"/api/history/{seeded['infy_decision'].decision_id}")
        assert detail.status_code == 200
        detail_payload = detail.json()["data"]
        assert detail_payload["decision"]["symbol"] == "INFY"
        assert detail_payload["backtest"]["matches"] == 5
        assert detail_payload["snapshot"]["decision_metrics"]["confidence"] == 78

        export = client.get("/api/history/export", params={"symbol": "INFY"})
        assert export.status_code == 200
        csv_rows = list(csv.reader(io.StringIO(export.text)))
        assert csv_rows[0][0] == "decision_id"
        assert csv_rows[1][1] == "INFY"
    finally:
        db.close()


def test_stock_chart_alerts_health_and_watchlist_cap(monkeypatch):
    client, SessionLocal = build_test_client()
    db = SessionLocal()
    try:
        seed_reference_data(db)

        monkeypatch.setattr(
            DataAgent,
            "get_chart_data",
            lambda self, symbol, period="6mo", interval="1d": [
                {"date": "2026-03-20", "open": 1490, "high": 1510, "low": 1488, "close": 1502, "volume": 3200000},
                {"date": "2026-03-21", "open": 1503, "high": 1521, "low": 1498, "close": 1514, "volume": 3400000},
            ],
        )

        chart = client.get("/api/stock/INFY/chart", params={"period": "6mo", "interval": "1d"})
        assert chart.status_code == 200
        chart_payload = chart.json()["data"]
        assert chart_payload["symbol"] == "INFY"
        assert len(chart_payload["ohlcv"]) == 2

        alerts = client.get("/api/alerts")
        assert alerts.status_code == 200
        alerts_payload = alerts.json()["data"]
        assert alerts_payload["unread_count"] == 1
        assert len(alerts_payload["alerts"]) == 2

        health = client.get("/api/health/")
        assert health.status_code == 200
        health_payload = health.json()["data"]
        assert health_payload["latest_scan"]["status"] == "running"
        assert "tinyfish" in health_payload

        for index in range(3, 22):
            symbol = f"SYM{index}"
            db.add(Stock(symbol=symbol, name=f"Stock {index}", sector="Synthetic"))
            db.add(WatchlistItem(user_id="default", symbol=symbol))
        db.commit()

        cap_response = client.post("/api/watchlist/RELIANCE")
        assert cap_response.status_code == 409
        assert "Watchlist limit reached" in cap_response.json()["detail"]
    finally:
        db.close()
