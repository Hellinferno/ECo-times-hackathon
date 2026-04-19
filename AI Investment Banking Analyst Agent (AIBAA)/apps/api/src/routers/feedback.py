"""Feedback router — user-submitted support/feedback chat threads.

Users create threads and post messages on their own threads. Admins see all
threads within their tenant and can reply or mark a thread resolved.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from db_models import FeedbackMessageModel, FeedbackThreadModel
from dependencies import AdminDep, CurrentUserDep, DbSessionDep
from models import APIResponse, Meta

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feedback", tags=["Feedback"])


_MAX_BODY = 4000
_MAX_SUBJECT = 200
_ADMIN_ROLE = "admin"


class FeedbackThreadCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=_MAX_SUBJECT)
    body: str = Field(..., min_length=1, max_length=_MAX_BODY)

    @field_validator("subject", "body", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v


class FeedbackMessageCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=_MAX_BODY)

    @field_validator("body", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v


class FeedbackThreadPatch(BaseModel):
    status: str = Field(..., pattern="^(open|resolved)$")


def _serialize_thread(t: FeedbackThreadModel, unread_for_admin: Optional[bool] = None) -> dict:
    data = {
        "thread_id": t.id,
        "subject": t.subject,
        "status": t.status,
        "created_by_user_id": t.created_by_user_id,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "last_activity_at": t.last_activity_at.isoformat() if t.last_activity_at else None,
    }
    if unread_for_admin is not None:
        data["unread_for_admin"] = unread_for_admin
    return data


def _serialize_message(m: FeedbackMessageModel) -> dict:
    return {
        "message_id": m.id,
        "thread_id": m.thread_id,
        "author_user_id": m.author_user_id,
        "author_role": m.author_role,
        "body": m.body,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def _meta() -> Meta:
    return Meta(request_id=f"req_{uuid.uuid4().hex[:8]}")


def _get_thread_or_404(db, thread_id: str, tenant_id: str) -> FeedbackThreadModel:
    thread = (
        db.query(FeedbackThreadModel)
        .filter(
            FeedbackThreadModel.id == thread_id,
            FeedbackThreadModel.tenant_id == tenant_id,
        )
        .first()
    )
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


def _require_thread_access(thread: FeedbackThreadModel, user) -> None:
    if user["role"].strip().lower() == _ADMIN_ROLE:
        return
    if thread.created_by_user_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not allowed to access this thread")


@router.get("/threads", response_model=APIResponse)
async def list_threads(db: DbSessionDep, current_user: CurrentUserDep):
    """List threads. Non-admin users see only their own; admins see all in tenant."""
    query = db.query(FeedbackThreadModel).filter(
        FeedbackThreadModel.tenant_id == current_user["tenant_id"]
    )
    if current_user["role"].strip().lower() != _ADMIN_ROLE:
        query = query.filter(FeedbackThreadModel.created_by_user_id == current_user["user_id"])

    threads = query.order_by(FeedbackThreadModel.last_activity_at.desc()).limit(200).all()
    return APIResponse(
        success=True,
        data={"threads": [_serialize_thread(t) for t in threads], "total": len(threads)},
        meta=_meta(),
    )


@router.post("/threads", response_model=APIResponse, status_code=201)
async def create_thread(
    payload: FeedbackThreadCreate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
):
    now = datetime.now(timezone.utc)
    role = current_user["role"].strip().lower()
    author_role = _ADMIN_ROLE if role == _ADMIN_ROLE else "user"

    thread = FeedbackThreadModel(
        id=str(uuid.uuid4()),
        tenant_id=current_user["tenant_id"],
        created_by_user_id=current_user["user_id"],
        subject=payload.subject,
        status="open",
        created_at=now,
        last_activity_at=now,
    )
    db.add(thread)
    db.flush()

    message = FeedbackMessageModel(
        id=str(uuid.uuid4()),
        thread_id=thread.id,
        author_user_id=current_user["user_id"],
        author_role=author_role,
        body=payload.body,
        created_at=now,
    )
    db.add(message)
    db.commit()
    db.refresh(thread)
    db.refresh(message)

    return APIResponse(
        success=True,
        data={"thread": _serialize_thread(thread), "message": _serialize_message(message)},
        meta=_meta(),
    )


@router.get("/threads/{thread_id}/messages", response_model=APIResponse)
async def list_messages(
    thread_id: str,
    db: DbSessionDep,
    current_user: CurrentUserDep,
):
    thread = _get_thread_or_404(db, thread_id, current_user["tenant_id"])
    _require_thread_access(thread, current_user)

    messages = (
        db.query(FeedbackMessageModel)
        .filter(FeedbackMessageModel.thread_id == thread_id)
        .order_by(FeedbackMessageModel.created_at.asc())
        .all()
    )
    return APIResponse(
        success=True,
        data={
            "thread": _serialize_thread(thread),
            "messages": [_serialize_message(m) for m in messages],
        },
        meta=_meta(),
    )


@router.post("/threads/{thread_id}/messages", response_model=APIResponse, status_code=201)
async def post_message(
    thread_id: str,
    payload: FeedbackMessageCreate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
):
    thread = _get_thread_or_404(db, thread_id, current_user["tenant_id"])
    _require_thread_access(thread, current_user)

    if thread.status != "open":
        raise HTTPException(status_code=409, detail="Thread is resolved; reopen it to reply")

    now = datetime.now(timezone.utc)
    role = current_user["role"].strip().lower()
    author_role = _ADMIN_ROLE if role == _ADMIN_ROLE else "user"

    message = FeedbackMessageModel(
        id=str(uuid.uuid4()),
        thread_id=thread_id,
        author_user_id=current_user["user_id"],
        author_role=author_role,
        body=payload.body,
        created_at=now,
    )
    thread.last_activity_at = now
    db.add(message)
    db.commit()
    db.refresh(message)

    return APIResponse(success=True, data=_serialize_message(message), meta=_meta())


@router.patch("/threads/{thread_id}", response_model=APIResponse)
async def update_thread_status(
    thread_id: str,
    payload: FeedbackThreadPatch,
    db: DbSessionDep,
    current_user: AdminDep,
):
    thread = _get_thread_or_404(db, thread_id, current_user["tenant_id"])
    thread.status = payload.status
    thread.last_activity_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(thread)

    return APIResponse(success=True, data=_serialize_thread(thread), meta=_meta())
