from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.db import Base, ExternalSignalEvent, WebFetchRun
from providers.web_intel_provider import NormalizedSignalEvent, WebIntelProvider
from services.web_intel_service import WebIntelService


class FakeProvider(WebIntelProvider):
    def run_goal_batch(self, goals, timeout_secs=20, max_concurrency=20):
        source_type = goals[0].source_type if goals else ""
        if source_type == "news_sentiment":
            raise RuntimeError("simulated provider failure")

        now = datetime.utcnow()
        events = []
        for goal in goals:
            payload = {"symbol": goal.symbol or "INFY", "score": 0.6, "sentiment": 0.4, "confidence": 0.8}
            events.append(
                NormalizedSignalEvent(
                    symbol=(goal.symbol or "INFY").upper(),
                    event_type=goal.source_type,
                    event_time=now,
                    source="tinyfish",
                    payload_json=payload,
                    strength=Decimal("0.60"),
                    sentiment=Decimal("0.40"),
                    confidence=Decimal("0.80"),
                    expires_at=now + timedelta(hours=1),
                    dedupe_hash=f"{goal.source_type}:{goal.symbol}:{now.isoformat()}",
                )
            )
        return events


def test_web_intel_service_fail_open_persists_partial_data():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        service = WebIntelService(db=db, provider=FakeProvider())
        summary = service.prefetch(symbols=["INFY", "TCS"], force=True)

        assert "sources" in summary
        assert summary["sources"]["news_sentiment"]["status"] == "failed"

        run_rows = db.query(WebFetchRun).all()
        assert len(run_rows) == 5

        event_rows = db.query(ExternalSignalEvent).all()
        assert len(event_rows) > 0
    finally:
        db.close()
