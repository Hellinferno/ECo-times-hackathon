"""Feedback — user-submitted support/feedback chat.

FeedbackThread groups messages into a conversation scoped to one organization.
FeedbackMessage is an append-only entry, authored by either the creating user
or an admin replying on the thread.

status: open | resolved
author_role: user | admin
"""
from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from .base import Base


class FeedbackThread(Base):
    __tablename__ = "feedback_threads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    created_by_user_id = Column(String(36), ForeignKey("platform_users.id"), nullable=False, index=True)
    subject = Column(String(200), nullable=False)
    status = Column(String(40), nullable=False, default="open", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    last_activity_at = Column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        index=True,
    )


class FeedbackMessage(Base):
    __tablename__ = "feedback_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(
        String(36),
        ForeignKey("feedback_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_user_id = Column(String(36), ForeignKey("platform_users.id"), nullable=False, index=True)
    author_role = Column(String(40), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
