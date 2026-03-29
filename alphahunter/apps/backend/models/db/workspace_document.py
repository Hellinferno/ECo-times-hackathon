"""WorkspaceDocument — file uploaded to a workspace.

parse_status: pending | processing | done | failed — tracks text extraction.
rag_status:   pending | indexing  | done | failed — tracks vector embedding.
classification: internal | confidential | public.

storage_path points to the blob storage key; text_preview holds the first
~500 chars extracted by the document parser for quick display.
"""
from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from .base import Base


class WorkspaceDocument(Base):
    __tablename__ = "workspace_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    uploaded_by = Column(String(36), ForeignKey("platform_users.id"), nullable=False, index=True)
    filename = Column(String(200), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size_bytes = Column(Integer, nullable=False, default=0)
    category = Column(String(60), nullable=True)
    classification = Column(String(40), nullable=False, default="internal")
    parse_status = Column(String(40), nullable=False, default="pending")
    rag_status = Column(String(40), nullable=False, default="pending")
    storage_path = Column(String(400), nullable=True)
    text_preview = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
