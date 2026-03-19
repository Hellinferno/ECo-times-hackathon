"""Webhooks router — CRUD for tenant webhook subscriptions."""
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db_models import WebhookModel
from dependencies import AdminDep, DbSessionDep
from models import APIResponse, Meta

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class WebhookCreate(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)
    event_types: list[str] = Field(default_factory=list)
    description: Optional[str] = None


class WebhookUpdate(BaseModel):
    url: Optional[str] = Field(default=None, min_length=1, max_length=2048)
    event_types: Optional[list[str]] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


def _serialize(w: WebhookModel) -> dict:
    return {
        "id": w.id,
        "url": w.url,
        "event_types": w.event_types or [],
        "is_active": w.is_active,
        "description": w.description,
        "created_at": w.created_at.isoformat() if w.created_at else None,
    }


@router.get("", response_model=APIResponse)
async def list_webhooks(db: DbSessionDep, current_user: AdminDep):
    tenant_id = current_user["tenant_id"]
    hooks = (
        db.query(WebhookModel)
        .filter(WebhookModel.tenant_id == tenant_id)
        .order_by(WebhookModel.created_at.desc())
        .all()
    )
    return APIResponse(
        success=True,
        data={"webhooks": [_serialize(h) for h in hooks]},
        meta=Meta(request_id=f"req_{uuid.uuid4().hex[:8]}"),
    )


@router.post("", response_model=APIResponse, status_code=201)
async def create_webhook(
    payload: WebhookCreate,
    db: DbSessionDep,
    current_user: AdminDep,
):
    hook = WebhookModel(
        id=str(uuid.uuid4()),
        tenant_id=current_user["tenant_id"],
        url=payload.url,
        event_types=payload.event_types,
        description=payload.description,
    )
    db.add(hook)
    db.commit()
    db.refresh(hook)
    return APIResponse(
        success=True,
        data=_serialize(hook),
        meta=Meta(request_id=f"req_{uuid.uuid4().hex[:8]}"),
    )


@router.patch("/{webhook_id}", response_model=APIResponse)
async def update_webhook(
    webhook_id: str,
    payload: WebhookUpdate,
    db: DbSessionDep,
    current_user: AdminDep,
):
    hook = (
        db.query(WebhookModel)
        .filter(
            WebhookModel.id == webhook_id,
            WebhookModel.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not hook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    if payload.url is not None:
        hook.url = payload.url
    if payload.event_types is not None:
        hook.event_types = payload.event_types
    if payload.is_active is not None:
        hook.is_active = payload.is_active
    if payload.description is not None:
        hook.description = payload.description

    db.commit()
    db.refresh(hook)
    return APIResponse(
        success=True,
        data=_serialize(hook),
        meta=Meta(request_id=f"req_{uuid.uuid4().hex[:8]}"),
    )


@router.delete("/{webhook_id}", response_model=APIResponse)
async def delete_webhook(
    webhook_id: str,
    db: DbSessionDep,
    current_user: AdminDep,
):
    hook = (
        db.query(WebhookModel)
        .filter(
            WebhookModel.id == webhook_id,
            WebhookModel.tenant_id == current_user["tenant_id"],
        )
        .first()
    )
    if not hook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    db.delete(hook)
    db.commit()
    return APIResponse(
        success=True,
        data={"deleted": webhook_id},
        meta=Meta(request_id=f"req_{uuid.uuid4().hex[:8]}"),
    )
