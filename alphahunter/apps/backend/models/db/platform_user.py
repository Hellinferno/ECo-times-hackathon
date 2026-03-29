"""PlatformUser — user account within an organization.

Roles: analyst | manager | admin.
auth_mode: demo (JWT-only) | sso (external IdP, future).
Every user is scoped to one organization via org_id.
"""
from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String

from .base import Base


class PlatformUser(Base):
    __tablename__ = "platform_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    username = Column(String(80), nullable=False, unique=True, index=True)
    email = Column(String(160), nullable=False, unique=True, index=True)
    role = Column(String(40), nullable=False, default="analyst", index=True)
    auth_mode = Column(String(40), nullable=False, default="demo")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
