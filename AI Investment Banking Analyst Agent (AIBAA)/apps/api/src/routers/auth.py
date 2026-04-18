import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Response

from audit import log_security_event
from dependencies import (
    CurrentUserDep,
    DbSessionDep,
    authenticate_demo_user,
    clear_session_cookie,
    create_access_token,
    revoke_token,
    set_session_cookie,
)
from models import APIResponse, CurrentUserResponse, LoginRequest, LoginResponse, Meta

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=APIResponse)
async def login(payload: LoginRequest, response: Response, request: Request, db: DbSessionDep):
    demo_user = authenticate_demo_user(payload.username, payload.password)
    token, expires_at = create_access_token(
        user_id=demo_user["user_id"],
        tenant_id=demo_user["tenant_id"],
        role=demo_user["role"],
        email=demo_user["email"],
    )
    set_session_cookie(response, token, expires_at)
    log_security_event(
        db=db,
        action="auth.login",
        tenant_id=demo_user["tenant_id"],
        user_id=demo_user["user_id"],
        resource_type="session",
        resource_id=demo_user["user_id"],
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details={"username": demo_user["username"], "role": demo_user["role"]},
    )
    return APIResponse(
        success=True,
        data=LoginResponse(
            user=CurrentUserResponse(
                user_id=demo_user["user_id"],
                tenant_id=demo_user["tenant_id"],
                role=demo_user["role"],
                email=demo_user["email"],
                token_id=None,
            ),
            session_expires_at=expires_at.isoformat(),
        ),
        meta=Meta(request_id=f"req_{uuid.uuid4().hex[:8]}"),
    )


@router.get("/me", response_model=APIResponse)
async def get_me(current_user: CurrentUserDep):
    return APIResponse(
        success=True,
        data=CurrentUserResponse(
            user_id=current_user["user_id"],
            tenant_id=current_user["tenant_id"],
            role=current_user["role"],
            email=current_user["email"],
            token_id=current_user["token_id"],
        ),
        meta=Meta(request_id=f"req_{uuid.uuid4().hex[:8]}"),
    )


@router.post("/logout", response_model=APIResponse)
async def logout(
    response: Response,
    request: Request,
    current_user: CurrentUserDep,
    db: DbSessionDep,
):
    if current_user.get("token_id"):
        now = datetime.now(timezone.utc).timestamp()
        exp = float(current_user["claims"].get("exp", now + 3600))
        revoke_token(current_user["token_id"], int(exp - now))

    clear_session_cookie(response)
    log_security_event(
        db=db,
        action="auth.logout",
        tenant_id=current_user["tenant_id"],
        user_id=current_user["user_id"],
        resource_type="session",
        resource_id=current_user.get("token_id"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return APIResponse(
        success=True,
        data={"message": "Logged out successfully"},
        meta=Meta(request_id=f"req_{uuid.uuid4().hex[:8]}"),
    )
