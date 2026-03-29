"""ScanResult — per-stock output of a single scan run iteration.

One row per (scan_run, symbol) pair — enforced by the uq_scan_result constraint.

Signal columns: breakout_triggered, volume_spike_triggered, bulk_deal_triggered
  plus extra_signals_json for the 4 enrichment signals.
composite_score (0–1) is the weighted blend used by the decision engine.
reasoning_text is the raw JSON string returned by ReasoningAgent (llm_summary +
  key_factors); parsed at read time by api/presenters.py.
backtest_* columns are populated by BacktestingAgent.
"""
from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, Text, ForeignKey, BigInteger, UniqueConstraint, Index, JSON
from .base import Base
import datetime

class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    scan_run_id = Column(Integer, ForeignKey('scan_runs.id', ondelete='CASCADE'), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    scanned_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    price = Column(Numeric(10, 2))
    volume_today = Column(BigInteger)
    volume_avg_20d = Column(BigInteger)
    volume_ratio = Column(Numeric(5, 2))

    breakout_triggered = Column(Boolean, nullable=False, default=False)
    volume_spike_triggered = Column(Boolean, nullable=False, default=False)
    bulk_deal_triggered = Column(Boolean, nullable=False, default=False)

    breakout_details = Column(JSON)
    volume_spike_details = Column(JSON)
    bulk_deal_details = Column(JSON)
    extra_signals_json = Column(JSON)
    data_quality_json = Column(JSON)

    signal_count = Column(Integer, nullable=False, default=0)
    composite_score = Column(Numeric(5, 4), index=True)

    reasoning_text = Column(Text)
    reasoning_generated_at = Column(DateTime)

    backtest_matches = Column(Integer)
    backtest_success_rate = Column(Numeric(5, 2))
    backtest_avg_return = Column(Numeric(6, 3))
    backtest_worst_case = Column(Numeric(6, 3))
    backtest_best_case = Column(Numeric(6, 3))
    backtest_cases_json = Column(JSON)

    __table_args__ = (
        UniqueConstraint('scan_run_id', 'symbol', name='uq_scan_result'),
    )

Index('idx_scan_results_composite', ScanResult.composite_score.desc())
