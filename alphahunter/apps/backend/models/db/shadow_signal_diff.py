from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, JSON, Index
from .base import Base
import datetime


class ShadowSignalDiff(Base):
    __tablename__ = "shadow_signal_diffs"

    id = Column(Integer, primary_key=True, index=True)
    scan_run_id = Column(Integer, ForeignKey("scan_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    legacy_score = Column(Numeric(6, 4), nullable=False, default=0)
    new_score = Column(Numeric(6, 4), nullable=False, default=0)
    legacy_action = Column(String(10), nullable=False)
    new_action = Column(String(10), nullable=False)
    diff_payload = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)


Index("idx_shadow_signal_diffs_run_symbol", ShadowSignalDiff.scan_run_id, ShadowSignalDiff.symbol)
