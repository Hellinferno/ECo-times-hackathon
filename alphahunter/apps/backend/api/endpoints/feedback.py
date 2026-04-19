"""Feedback endpoint — user-submitted support/feedback chat threads.

Users create threads and post messages on their own threads within their org.
Admins see all threads in the org, can reply, and can resolve/reopen threads.
"""
from __future__ import annotations

import datetime
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from api.security import CurrentUserDep, DbSessionDep, require_roles
from models.db import FeedbackMessage, FeedbackThread


router = APIRouter(prefix="/feedback", tags=["feedback"])

_MAX_BODY = 4000
_MAX_SUBJECT = 200
_ADMIN_ROLE = "admin"

AdminUserDep = Annotated[dict[str, Any], Depends(require_roles("admin"))]


class ThreadCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=_MAX_SUBJECT)
    body: str = Field(..., min_length=1, max_length=_MAX_BODY)

    @field_validator("subject", "body", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v


class MessageCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=_MAX_BODY)

    @field_validator("body", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v


class ThreadPatch(BaseModel):
    status: str = Field(..., pattern="^(open|resolved)$")


def _ok(data: Any) -> dict[str, Any]:
    return {"success": True, "data": data}


def _serialize_thread(t: FeedbackThread) -> dict[str, Any]:
    return {
        "thread_id": t.id,
        "subject": t.subject,
        "status": t.status,
        "created_by_user_id": t.created_by_user_id,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "last_activity_at": t.last_activity_at.isoformat() if t.last_activity_at else None,
    }


def _serialize_message(m: FeedbackMessage) -> dict[str, Any]:
    return {
        "message_id": m.id,
        "thread_id": m.thread_id,
        "author_user_id": m.author_user_id,
        "author_role": m.author_role,
        "body": m.body,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def _get_thread_or_404(db: Session, thread_id: str, org_id: str) -> FeedbackThread:
    thread = (
        db.query(FeedbackThread)
        .filter(FeedbackThread.id == thread_id, FeedbackThread.org_id == org_id)
        .first()
    )
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


def _ensure_thread_access(thread: FeedbackThread, user: dict[str, Any]) -> None:
    if user["role"].lower() == _ADMIN_ROLE:
        return
    if thread.created_by_user_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not allowed to access this thread")


@router.get("/threads")
def list_threads(db: DbSessionDep, current_user: CurrentUserDep) -> dict[str, Any]:
    query = db.query(FeedbackThread).filter(FeedbackThread.org_id == current_user["org_id"])
    if current_user["role"].lower() != _ADMIN_ROLE:
        query = query.filter(FeedbackThread.created_by_user_id == current_user["user_id"])
    threads = query.order_by(FeedbackThread.last_activity_at.desc()).limit(200).all()
    return _ok({"threads": [_serialize_thread(t) for t in threads], "total": len(threads)})


@router.post("/threads", status_code=status.HTTP_201_CREATED)
def create_thread(
    payload: ThreadCreate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict[str, Any]:
    now = datetime.datetime.utcnow()
    role = current_user["role"].lower()
    author_role = _ADMIN_ROLE if role == _ADMIN_ROLE else "user"

    thread = FeedbackThread(
        id=str(uuid.uuid4()),
        org_id=current_user["org_id"],
        created_by_user_id=current_user["user_id"],
        subject=payload.subject,
        status="open",
        created_at=now,
        last_activity_at=now,
    )
    db.add(thread)
    db.flush()

    message = FeedbackMessage(
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

    return _ok({"thread": _serialize_thread(thread), "message": _serialize_message(message)})


@router.get("/threads/{thread_id}/messages")
def list_messages(
    thread_id: str,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict[str, Any]:
    thread = _get_thread_or_404(db, thread_id, current_user["org_id"])
    _ensure_thread_access(thread, current_user)
    messages = (
        db.query(FeedbackMessage)
        .filter(FeedbackMessage.thread_id == thread_id)
        .order_by(FeedbackMessage.created_at.asc())
        .all()
    )
    return _ok(
        {
            "thread": _serialize_thread(thread),
            "messages": [_serialize_message(m) for m in messages],
        }
    )


@router.post("/threads/{thread_id}/messages", status_code=status.HTTP_201_CREATED)
def post_message(
    thread_id: str,
    payload: MessageCreate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict[str, Any]:
    thread = _get_thread_or_404(db, thread_id, current_user["org_id"])
    _ensure_thread_access(thread, current_user)

    if thread.status != "open":
        raise HTTPException(status_code=409, detail="Thread is resolved; reopen it to reply")

    now = datetime.datetime.utcnow()
    role = current_user["role"].lower()
    author_role = _ADMIN_ROLE if role == _ADMIN_ROLE else "user"

    message = FeedbackMessage(
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

    return _ok(_serialize_message(message))


@router.patch("/threads/{thread_id}")
def patch_thread(
    thread_id: str,
    payload: ThreadPatch,
    db: DbSessionDep,
    current_user: AdminUserDep,
) -> dict[str, Any]:
    thread = _get_thread_or_404(db, thread_id, current_user["org_id"])
    thread.status = payload.status
    thread.last_activity_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(thread)
    return _ok(_serialize_thread(thread))
