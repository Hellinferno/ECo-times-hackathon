"""WorkspaceOutput — a versioned, reviewable research output.

output_type: memo | model | report | slide_deck.
review_status: draft | in_review | approved | rejected.
source_kind: valuation | agent_run | manual.

version increments each time an output is regenerated.
preview_markdown holds rendered content for in-app display;
storage_path points to the full document in blob storage.
"""
from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from .base import Base


class WorkspaceOutput(Base):
    __tablename__ = "workspace_outputs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    source_run_id = Column(String(36), nullable=True, index=True)
    source_kind = Column(String(40), nullable=False, default="valuation")
    output_type = Column(String(40), nullable=False, index=True)
    review_status = Column(String(40), nullable=False, default="draft", index=True)
    version = Column(Integer, nullable=False, default=1)
    title = Column(String(200), nullable=False)
    preview_markdown = Column(Text, nullable=True)
    storage_path = Column(String(400), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
