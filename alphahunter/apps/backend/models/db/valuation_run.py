"""ValuationRun — record of a DCF / LBO / Comps valuation calculation.

model_type: dcf | lbo | comps | sum_of_parts.
status: queued | running | completed | failed.

assumptions_json holds the analyst-supplied inputs; result_summary_json
stores the computed output ranges; warnings_json captures data-quality
caveats produced by the valuation engine.
"""
from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String

from .base import Base


class ValuationRun(Base):
    __tablename__ = "valuation_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    requested_by = Column(String(36), ForeignKey("platform_users.id"), nullable=False, index=True)
    model_type = Column(String(40), nullable=False, index=True)
    status = Column(String(40), nullable=False, default="queued", index=True)
    assumptions_json = Column(JSON, nullable=False, default=dict)
    result_summary_json = Column(JSON, nullable=True)
    warnings_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
