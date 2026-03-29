"""WorkspaceAgentRun — execution record for an AI agent task.

agent_type: research | valuation | document_qa | macro.
status: queued | running | completed | failed.

parameters_json holds the task inputs; summary stores the agent's
narrative output; confidence (0–100) reflects the agent's self-assessed
certainty. error_message is populated on failure.
"""
from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, JSON, Numeric, String, Text

from .base import Base


class WorkspaceAgentRun(Base):
    __tablename__ = "workspace_agent_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    requested_by = Column(String(36), ForeignKey("platform_users.id"), nullable=False, index=True)
    agent_type = Column(String(40), nullable=False, index=True)
    task_name = Column(String(80), nullable=False)
    status = Column(String(40), nullable=False, default="queued", index=True)
    parameters_json = Column(JSON, nullable=False, default=dict)
    summary = Column(Text, nullable=True)
    confidence = Column(Numeric(5, 2), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
