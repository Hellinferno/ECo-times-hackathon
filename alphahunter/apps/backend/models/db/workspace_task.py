"""WorkspaceTask — checklist item within a workspace.

status: todo | in_progress | done | blocked.
priority: low | medium | high | critical.
owner_label defaults to "AI Copilot" for auto-generated tasks;
set to a username for human-assigned tasks.
"""
from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from .base import Base


class WorkspaceTask(Base):
    __tablename__ = "workspace_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    title = Column(String(180), nullable=False)
    status = Column(String(40), nullable=False, default="todo", index=True)
    priority = Column(String(40), nullable=False, default="medium")
    owner_label = Column(String(80), nullable=False, default="AI Copilot")
    description = Column(Text, nullable=True)
    due_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
