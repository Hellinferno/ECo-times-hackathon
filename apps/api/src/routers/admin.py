"""Admin router — tenant management and security audit log."""
import uuid
import logging

from fastapi import APIRouter, HTTPException

from db_models import SecurityAuditLogModel
from dependencies import AdminDep, DbSessionDep
from models import APIResponse, Meta

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/audit-log", response_model=APIResponse)
async def list_audit_log(
    db: DbSessionDep,
    current_user: AdminDep,
    limit: int = 50,
    offset: int = 0,
):
    """Return recent security audit log entries (admin only)."""
    tenant_id = current_user["tenant_id"]
    query = (
        db.query(SecurityAuditLogModel)
        .filter(SecurityAuditLogModel.tenant_id == tenant_id)
        .order_by(SecurityAuditLogModel.created_at.desc())
    )
    total = query.count()
    entries = query.offset(offset).limit(min(limit, 200)).all()

    return APIResponse(
        success=True,
        data={
            "entries": [
                {
                    "id": e.id,
                    "action": e.action,
                    "user_id": e.user_id,
                    "resource_type": e.resource_type,
                    "resource_id": e.resource_id,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in entries
            ],
            "total": total,
        },
        meta=Meta(request_id=f"req_{uuid.uuid4().hex[:8]}"),
    )
