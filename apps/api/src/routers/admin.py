"""Admin router with audit log, model registry, and eval report endpoints."""
from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from db_models import SecurityAuditLogModel
from dependencies import AdminDep, DbSessionDep
from model_registry import (
    DEFAULT_PURPOSE,
    list_registry_entries,
    promote_registry_entry,
    rollback_registry_entry,
    serialize_registry_entry,
    stage_registry_entry,
    validate_staged_entry,
)
from models import (
    APIResponse,
    Meta,
    ModelRegistryPromoteRequest,
    ModelRegistryRollbackRequest,
    ModelRegistryStageRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])
_EVAL_REPORTS_DIR = Path(__file__).resolve().parents[5] / "evals" / "aibaa" / "reports"


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


@router.get("/model-registry", response_model=APIResponse)
async def get_model_registry(
    db: DbSessionDep,
    current_user: AdminDep,
):
    entries = list_registry_entries(db, tenant_id=current_user["tenant_id"])
    return APIResponse(
        success=True,
        data={"entries": [serialize_registry_entry(entry) for entry in entries]},
        meta=Meta(request_id=f"req_{uuid.uuid4().hex[:8]}"),
    )


@router.post("/model-registry/stage", response_model=APIResponse)
async def stage_model_registry_entry(
    payload: ModelRegistryStageRequest,
    db: DbSessionDep,
    current_user: AdminDep,
    purpose: str = Query(default=DEFAULT_PURPOSE),
):
    entry = stage_registry_entry(
        db,
        tenant_id=current_user["tenant_id"],
        purpose=purpose,
        provider=payload.provider,
        model_name=payload.model_name,
        prompt_version=payload.prompt_version,
        config=payload.config,
        created_by=current_user["user_id"],
    )
    return APIResponse(
        success=True,
        data=serialize_registry_entry(entry),
        meta=Meta(request_id=f"req_{uuid.uuid4().hex[:8]}"),
    )


@router.post("/model-registry/validate", response_model=APIResponse)
async def validate_model_registry_entry(
    payload: ModelRegistryPromoteRequest,
    db: DbSessionDep,
    current_user: AdminDep,
):
    try:
        entry = validate_staged_entry(db, entry_id=payload.entry_id, tenant_id=current_user["tenant_id"])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return APIResponse(
        success=True,
        data=serialize_registry_entry(entry),
        meta=Meta(request_id=f"req_{uuid.uuid4().hex[:8]}"),
    )


@router.post("/model-registry/promote", response_model=APIResponse)
async def promote_model_registry(
    payload: ModelRegistryPromoteRequest,
    db: DbSessionDep,
    current_user: AdminDep,
    purpose: str = Query(default=DEFAULT_PURPOSE),
):
    try:
        entry = promote_registry_entry(
            db,
            tenant_id=current_user["tenant_id"],
            purpose=purpose,
            entry_id=payload.entry_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return APIResponse(
        success=True,
        data=serialize_registry_entry(entry),
        meta=Meta(request_id=f"req_{uuid.uuid4().hex[:8]}"),
    )


@router.post("/model-registry/rollback", response_model=APIResponse)
async def rollback_model_registry(
    payload: ModelRegistryRollbackRequest,
    db: DbSessionDep,
    current_user: AdminDep,
    purpose: str = Query(default=DEFAULT_PURPOSE),
):
    try:
        entry = rollback_registry_entry(
            db,
            tenant_id=current_user["tenant_id"],
            purpose=purpose,
            entry_id=payload.entry_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return APIResponse(
        success=True,
        data=serialize_registry_entry(entry),
        meta=Meta(request_id=f"req_{uuid.uuid4().hex[:8]}"),
    )


@router.get("/model-registry/{entry_id}/eval-report", response_model=APIResponse)
async def get_model_registry_eval_report(
    entry_id: str,
    db: DbSessionDep,
    current_user: AdminDep,
):
    entries = list_registry_entries(db, tenant_id=current_user["tenant_id"])
    match = next((entry for entry in entries if entry.id == entry_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Registry entry not found")
    serialized = serialize_registry_entry(match)
    return APIResponse(
        success=True,
        data={
            "entry_id": entry_id,
            "eval_summary": serialized.get("eval_summary", {}),
            "validation_report": serialized.get("validation_report", {}),
            "canary_status": serialized.get("canary_status", "pending"),
            "rollout_notes": serialized.get("rollout_notes", ""),
        },
        meta=Meta(request_id=f"req_{uuid.uuid4().hex[:8]}"),
    )


@router.get("/eval-runs", response_model=APIResponse)
async def list_eval_runs(current_user: AdminDep):
    _ = current_user
    reports = []
    if _EVAL_REPORTS_DIR.exists():
        for path in sorted(_EVAL_REPORTS_DIR.glob("*.json"), reverse=True):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                payload = {}
            reports.append(
                {
                    "name": path.name,
                    "status": payload.get("status", "unknown"),
                    "task": payload.get("task"),
                    "generated_at": payload.get("generated_at"),
                }
            )
    return APIResponse(
        success=True,
        data={"reports": reports},
        meta=Meta(request_id=f"req_{uuid.uuid4().hex[:8]}"),
    )


@router.get("/eval-runs/{report_name}", response_model=APIResponse)
async def get_eval_run_report(report_name: str, current_user: AdminDep):
    _ = current_user
    safe_name = Path(report_name).name
    if safe_name != report_name or not safe_name.endswith(".json"):
        raise HTTPException(status_code=400, detail="Invalid report name")
    report_path = _EVAL_REPORTS_DIR / safe_name
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Eval report not found")
    return APIResponse(
        success=True,
        data=json.loads(report_path.read_text(encoding="utf-8")),
        meta=Meta(request_id=f"req_{uuid.uuid4().hex[:8]}"),
    )
