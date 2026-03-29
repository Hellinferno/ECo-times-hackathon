"""AuditLog — structured operational event log.

level: DEBUG | INFO | WARNING | ERROR.
module: the agent or service that emitted the event (e.g. "DataAgent").
duration_ms records execution time for performance-sensitive events.
Intended for internal observability — not exposed to end users.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from .base import Base
import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    level = Column(String(10), nullable=False, index=True)
    module = Column(String(50), nullable=False, index=True)
    event = Column(String(100), nullable=False)
    detail = Column(Text)
    symbol = Column(String(20))
    scan_run_id = Column(Integer)
    duration_ms = Column(Integer)

Index('idx_audit_logs_timestamp', AuditLog.timestamp.desc())
