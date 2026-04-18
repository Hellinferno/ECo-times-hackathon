"""Security audit logging helpers with integrity chaining."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

from sqlalchemy.orm import Session

from db_models import SecurityAuditLogModel


def _canonical_payload(
    *,
    entry_id: str,
    tenant_id: Optional[str],
    user_id: Optional[str],
    action: str,
    resource_type: Optional[str],
    resource_id: Optional[str],
    ip_address: Optional[str],
    user_agent: Optional[str],
    request_id: Optional[str],
    details: Optional[dict[str, Any]],
    created_at: datetime,
) -> str:
    payload = {
        "id": entry_id,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "request_id": request_id,
        "details": details or {},
        "created_at": created_at.isoformat(),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _compute_integrity_hash(prev_hash: str | None, payload: str) -> str:
    digest = hashlib.sha256()
    digest.update((prev_hash or "").encode("utf-8"))
    digest.update(payload.encode("utf-8"))
    return digest.hexdigest()


def log_security_event(
    db: Session,
    *,
    action: str,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> SecurityAuditLogModel:
    previous = (
        db.query(SecurityAuditLogModel)
        .filter(SecurityAuditLogModel.tenant_id == tenant_id)
        .order_by(SecurityAuditLogModel.created_at.desc(), SecurityAuditLogModel.id.desc())
        .first()
    )
    prev_hash = previous.integrity_hash if previous else None
    created_at = datetime.now(timezone.utc)
    entry_id = str(uuid.uuid4())
    payload = _canonical_payload(
        entry_id=entry_id,
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        details=details,
        created_at=created_at,
    )
    integrity_hash = _compute_integrity_hash(prev_hash, payload)

    entry = SecurityAuditLogModel(
        id=entry_id,
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        details=details,
        prev_hash=prev_hash,
        integrity_hash=integrity_hash,
        created_at=created_at,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def validate_audit_chain(entries: Iterable[SecurityAuditLogModel]) -> bool:
    previous_hash: str | None = None
    for entry in entries:
        payload = _canonical_payload(
            entry_id=entry.id,
            tenant_id=entry.tenant_id,
            user_id=entry.user_id,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            ip_address=entry.ip_address,
            user_agent=entry.user_agent,
            request_id=entry.request_id,
            details=entry.details,
            created_at=entry.created_at,
        )
        if entry.prev_hash != previous_hash:
            return False
        if entry.integrity_hash != _compute_integrity_hash(previous_hash, payload):
            return False
        previous_hash = entry.integrity_hash
    return True


def build_audit_csv(entries: Iterable[SecurityAuditLogModel]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "created_at",
            "tenant_id",
            "user_id",
            "action",
            "resource_type",
            "resource_id",
            "request_id",
            "ip_address",
            "user_agent",
            "prev_hash",
            "integrity_hash",
            "details",
        ]
    )
    for entry in entries:
        writer.writerow(
            [
                entry.id,
                entry.created_at.isoformat() if entry.created_at else "",
                entry.tenant_id or "",
                entry.user_id or "",
                entry.action,
                entry.resource_type or "",
                entry.resource_id or "",
                entry.request_id or "",
                entry.ip_address or "",
                entry.user_agent or "",
                entry.prev_hash or "",
                entry.integrity_hash or "",
                json.dumps(entry.details or {}, sort_keys=True),
            ]
        )
    return buffer.getvalue()
