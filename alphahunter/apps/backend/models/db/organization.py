"""Organization — top-level multi-tenant entity.

Every user and workspace belongs to exactly one organization.
The slug is the human-readable, URL-safe identifier used in API paths.
"""
from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, String

from .base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String(80), unique=True, nullable=False, index=True)
    name = Column(String(160), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
