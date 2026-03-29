"""Workspace — research workspace scoped to a company.

workspace_type: due_diligence | valuation | competitive_analysis | general.
stage: active | archived | completed.

Optionally linked back to the signal pipeline via source_symbol /
source_decision_id so that an analyst can trace a workspace to the
AlphaHunter scan that surfaced the opportunity.
"""
from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text

from .base import Base


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    owner_id = Column(String(36), ForeignKey("platform_users.id"), nullable=False, index=True)
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    workspace_type = Column(String(40), nullable=False, index=True)
    title = Column(String(180), nullable=False)
    stage = Column(String(40), nullable=False, default="active", index=True)
    source_symbol = Column(String(20), nullable=True, index=True)
    source_decision_id = Column(String(40), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    health_summary = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
