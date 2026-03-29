"""WebFetchRun — execution record for a TinyFish / web-intel prefetch batch.

source_type: tinyfish | generic_web.
status: running | completed | failed.
symbols_count / success_count track batch coverage.
error_summary stores a truncated message from the first unrecoverable error.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Uuid, Index
from .base import Base
import datetime
import uuid


class WebFetchRun(Base):
    __tablename__ = "web_fetch_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Uuid, unique=True, nullable=False, default=uuid.uuid4)
    source_type = Column(String(40), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="running", index=True)
    symbols_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    duration_ms = Column(Integer)
    error_summary = Column(Text)
    started_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    completed_at = Column(DateTime)


Index("idx_web_fetch_runs_started_at", WebFetchRun.started_at.desc())
