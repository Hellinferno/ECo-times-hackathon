"""JWT authentication and user identity helpers.

This module implements a minimal HS256 JWT stack without third-party JWT
libraries so that the dependency surface stays small.

Sections
--------
- Base64url helpers    — encode/decode without padding
- JWT operations       — create_access_token, decode_access_token
- Demo identity        — seed org + 3 demo users on first use
- Authentication       — authenticate_demo_user, serialize_user
- FastAPI dependencies — get_current_user, require_roles + typed Annotated aliases
"""
from __future__ import annotations

import base64
import datetime
import hashlib
import hmac
import json
import uuid
from typing import Annotated, Any, Callable

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models.db import Organization, PlatformUser


# ── Base64url helpers ──────────────────────────────────────────────────────────

def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(f"{raw}{padding}".encode("ascii"))


def _sign(message: bytes) -> str:
    digest = hmac.new(
        settings.AUTH_JWT_SECRET.encode("utf-8"),
        message,
        hashlib.sha256,
    ).digest()
    return _b64url_encode(digest)


# ── JWT operations ─────────────────────────────────────────────────────────────

def create_access_token(user: PlatformUser, org: Organization) -> tuple[str, str]:
    """Return (encoded_jwt, expires_at_iso) for the given user."""
    issued_at = datetime.datetime.now(datetime.timezone.utc)
    expires_at = issued_at + datetime.timedelta(minutes=max(5, settings.AUTH_JWT_EXPIRE_MINUTES))

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user.id,
        "org_id": org.id,
        "org_slug": org.slug,
        "role": user.role,
        "email": user.email,
        "username": user.username,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": f"tok_{uuid.uuid4().hex}",
    }

    encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(f"{encoded_header}.{encoded_payload}".encode("ascii"))
    return f"{encoded_header}.{encoded_payload}.{signature}", expires_at.isoformat()


def decode_access_token(token: str) -> dict[str, Any]:
    """Validate and decode a JWT. Raises HTTP 401 on any failure."""
    try:
        encoded_header, encoded_payload, signature = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token") from exc

    signed_portion = f"{encoded_header}.{encoded_payload}".encode("ascii")
    if not hmac.compare_digest(signature, _sign(signed_portion)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature")

    try:
        header = json.loads(_b64url_decode(encoded_header))
        payload = json.loads(_b64url_decode(encoded_payload))
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload") from exc

    if header.get("alg") != "HS256":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unsupported token algorithm")

    now_ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    if int(payload.get("exp", 0)) < now_ts:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

    return payload


# ── Demo identity ──────────────────────────────────────────────────────────────

_DEMO_PROFILES = {
    "analyst": {"username": "analyst", "email": "analyst@alphahunter.local", "role": "analyst"},
    "reviewer": {"username": "reviewer", "email": "reviewer@alphahunter.local", "role": "reviewer"},
    "admin": {"username": "admin", "email": "admin@alphahunter.local", "role": "admin"},
}


def ensure_demo_identities(db: Session) -> tuple[Organization, dict[str, PlatformUser]]:
    """Idempotently create the demo org and its three users."""
    org = db.query(Organization).filter(Organization.slug == settings.AUTH_DEMO_ORG_SLUG).first()
    if org is None:
        org = Organization(slug=settings.AUTH_DEMO_ORG_SLUG, name=settings.AUTH_DEMO_ORG_NAME)
        db.add(org)
        db.commit()
        db.refresh(org)

    users: dict[str, PlatformUser] = {}
    for key, profile in _DEMO_PROFILES.items():
        user = db.query(PlatformUser).filter(PlatformUser.username == profile["username"]).first()
        if user is None:
            user = PlatformUser(
                org_id=org.id,
                username=profile["username"],
                email=profile["email"],
                role=profile["role"],
                auth_mode="demo",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        users[key] = user

    return org, users


# ── Authentication ─────────────────────────────────────────────────────────────

def authenticate_demo_user(db: Session, username: str, password: str) -> tuple[Organization, PlatformUser]:
    """Validate demo credentials and return the matching (org, user) pair."""
    if password != settings.AUTH_DEMO_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    org, users = ensure_demo_identities(db)
    normalized = username.strip().lower()

    for user in users.values():
        if normalized in {user.username.lower(), user.email.lower(), user.role.lower()}:
            return org, user

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


def serialize_user(user: PlatformUser, org: Organization) -> dict[str, Any]:
    return {
        "id": user.id,
        "org_id": org.id,
        "org_slug": org.slug,
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }


# ── FastAPI dependencies ───────────────────────────────────────────────────────

def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """Validate the Bearer token and return the resolved user context."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
        )

    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)

    user = db.query(PlatformUser).filter(PlatformUser.id == payload.get("sub")).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive or missing")

    org = db.query(Organization).filter(Organization.id == user.org_id).first()
    if org is None or not org.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Organization is inactive or missing")

    return {
        "claims": payload,
        "user": user,
        "org": org,
        "user_id": user.id,
        "org_id": org.id,
        "org_slug": org.slug,
        "role": user.role,
        "email": user.email,
        "username": user.username,
    }


def require_roles(*roles: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Return a FastAPI dependency that enforces one of the given roles."""
    normalized_roles = {role.strip().lower() for role in roles if role.strip()}

    def dependency(current_user: Annotated[dict[str, Any], Depends(get_current_user)]) -> dict[str, Any]:
        if current_user["role"].lower() not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user['role']}' is not allowed for this action",
            )
        return current_user

    return dependency


# Typed shorthand aliases for use as endpoint parameters
DbSessionDep   = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[dict[str, Any], Depends(get_current_user)]
ReviewerUserDep = Annotated[dict[str, Any], Depends(require_roles("reviewer", "admin"))]
