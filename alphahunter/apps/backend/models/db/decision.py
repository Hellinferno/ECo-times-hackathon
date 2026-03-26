from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, Index, Uuid, JSON
from .base import Base
import datetime
import uuid

class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(Uuid, unique=True, nullable=False, default=uuid.uuid4)
    scan_result_id = Column(Integer, ForeignKey('scan_results.id'))
    symbol = Column(String(20), nullable=False, index=True)
    decided_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    action = Column(String(10), nullable=False, index=True)
    confidence = Column(Numeric(5, 2), nullable=False)

    entry_price = Column(Numeric(10, 2))
    target_price = Column(Numeric(10, 2))
    stop_loss = Column(Numeric(10, 2))
    rr_ratio = Column(Numeric(5, 2))

    score_signal = Column(Numeric(5, 4))
    score_backtest = Column(Numeric(5, 4))
    score_composite = Column(Numeric(5, 4))

    snapshot_json = Column(JSON, nullable=False)

    outcome_measured = Column(Boolean, nullable=False, default=False)
    outcome_measure_at = Column(DateTime)
    outcome_exit_price = Column(Numeric(10, 2))
    outcome_return_pct = Column(Numeric(6, 3))
    outcome_result = Column(String(10), index=True)
    outcome_measured_at = Column(DateTime)

Index('idx_decisions_decided_at', Decision.decided_at.desc())
