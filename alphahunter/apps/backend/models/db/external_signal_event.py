"""ExternalSignalEvent — cached enrichment signal from TinyFish or other web-intel sources.

event_type: news_sentiment | social_sentiment | insider_filing | macro_context.
expires_at controls TTL; the pipeline skips stale events (expires_at < now).
dedupe_hash is a SHA-256 of (symbol, event_type, source, payload) so that
re-fetching the same event doesn't create duplicates.
"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, JSON, UniqueConstraint, Index
from .base import Base
import datetime


class ExternalSignalEvent(Base):
    __tablename__ = "external_signal_events"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    event_type = Column(String(40), nullable=False, index=True)
    event_time = Column(DateTime, nullable=False, index=True)
    source = Column(String(50), nullable=False, default="tinyfish")
    payload_json = Column(JSON, nullable=False, default={})
    strength = Column(Numeric(6, 4))
    sentiment = Column(Numeric(6, 4))
    confidence = Column(Numeric(6, 4))
    expires_at = Column(DateTime, nullable=False, index=True)
    dedupe_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("dedupe_hash", name="uq_external_signal_event_dedupe"),
    )


Index("idx_external_signal_event_symbol_type_time", ExternalSignalEvent.symbol, ExternalSignalEvent.event_type, ExternalSignalEvent.event_time.desc())
