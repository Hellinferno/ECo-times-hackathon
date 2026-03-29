"""ScanRun — metadata record for one full pipeline execution.

triggered_by: manual | scheduler.
status: running | completed | failed.
duration_secs is derived from completed_at - started_at and stored for
quick dashboard display without recalculation.
"""
from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, Text, text, Index, Uuid
from .base import Base
import datetime
import uuid

class ScanRun(Base):
    __tablename__ = "scan_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Uuid, unique=True, nullable=False, default=uuid.uuid4)
    triggered_by = Column(String(20), nullable=False, default='scheduler')
    started_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    completed_at = Column(DateTime)
    status = Column(String(20), nullable=False, default='running', index=True)
    stocks_scanned = Column(Integer, default=0)
    signals_found = Column(Integer, default=0)
    error_message = Column(Text)
    duration_secs = Column(Numeric(6, 2))

Index('idx_scan_runs_started_at', ScanRun.started_at.desc())
