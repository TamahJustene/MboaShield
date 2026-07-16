"""Administrative user management (Phase 6)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from ...identity_store import admin_create_user, admin_update_user, list_users, write_auth_event
from ...repositories import get_user, write_audit_log
from ...schemas import AdminUserCreateIn, AdminUserUpdateIn, UserOut
from ..deps import get_current_user, require_permission

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


def _user_out(user: dict) -> UserOut:
    return UserOut(
        id=user["id"],
        display_name=user["display_name"],
        email=user.get("email"),
        role=user["role"],
        created_at=user["created_at"],
        is_active=bool(user.get("is_active", True)),
        mfa_enabled=bool(user.get("mfa_enabled", False)),
        auth_provider=user.get("auth_provider") or "local",
        must_reset_password=bool(user.get("must_reset_password", False)),
        last_login_at=user.get("last_login_at"),
    )


@router.get("")
def admin_list_users(
    role: str | None = None,
    q: str | None = None,
    limit: int = 100,
    _actor: dict | None = Depends(require_permission("users:manage")),
):
    items = list_users(role=role, q=q, limit=limit)
    return {"users": [_user_out(item) for item in items], "count": len(items)}


@router.post("")
def admin_create(
    body: AdminUserCreateIn,
    request: Request,
    actor: dict | None = Depends(require_permission("users:manage")),
):
    try:
        created = admin_create_user(
            display_name=body.display_name,
            email=body.email,
            role=body.role,
            password=body.password,
            invited_by_user_id=actor["id"] if actor else None,
            must_reset_password=body.must_reset_password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    write_audit_log(
        action="admin.user_create",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="user",
        resource_id=str(created["id"]),
        ip_address=ip,
        user_agent=ua,
        details={"role": created["role"]},
    )
    write_auth_event(
        event_type="admin.user_create",
        user_id=actor["id"] if actor else None,
        ip_address=ip,
        user_agent=ua,
        details={"target_user_id": created["id"]},
    )
    return {
        "user": _user_out(created),
        "temporary_password": created.get("temporary_password"),
    }


@router.get("/{user_id}", response_model=UserOut)
def admin_get_user(
    user_id: int,
    _actor: dict | None = Depends(require_permission("users:manage")),
):
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_out(user)


@router.patch("/{user_id}", response_model=UserOut)
def admin_patch_user(
    user_id: int,
    body: AdminUserUpdateIn,
    request: Request,
    actor: dict | None = Depends(require_permission("users:manage")),
):
    try:
        updated = admin_update_user(
            user_id,
            role=body.role,
            is_active=body.is_active,
            display_name=body.display_name,
            must_reset_password=body.must_reset_password,
        )
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    write_audit_log(
        action="admin.user_update",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="user",
        resource_id=str(user_id),
        ip_address=ip,
        user_agent=ua,
        details=body.model_dump(exclude_none=True),
    )
    return _user_out(updated)
