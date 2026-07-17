"""SCIM 2.0 Users - read + create (CI-1)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ...core.openapi_pillars import PILLAR_IDENTITY
from ...identity_store import admin_create_user, list_users
from ...repositories import write_audit_log
from ..deps import require_permission

router = APIRouter(prefix="/scim/v2", tags=[PILLAR_IDENTITY])


def _to_scim_user(user: dict, *, include_temp_password: bool = False) -> dict:
    payload = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": str(user["id"]),
        "userName": user.get("email") or f"user-{user['id']}",
        "displayName": user.get("display_name"),
        "active": bool(user.get("is_active", True)),
        "emails": (
            [{"value": user["email"], "primary": True, "type": "work"}]
            if user.get("email")
            else []
        ),
        "roles": [{"value": user.get("role") or "citizen", "primary": True}],
        "meta": {
            "resourceType": "User",
            "created": user.get("created_at"),
            "lastModified": user.get("last_login_at") or user.get("created_at"),
            "location": f"/scim/v2/Users/{user['id']}",
        },
        "urn:ietf:params:scim:schemas:extension:mboashield:2.0:User": {
            "auth_provider": user.get("auth_provider") or "local",
            "mfa_enabled": bool(user.get("mfa_enabled", False)),
        },
    }
    if include_temp_password and user.get("temporary_password"):
        payload["urn:ietf:params:scim:schemas:extension:mboashield:2.0:User"][
            "temporary_password"
        ] = user["temporary_password"]
    return payload


@router.get("/ServiceProviderConfig")
def scim_service_provider_config():
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
        "documentationUri": "https://github.com/TamahJustene/MboaShield",
        "patch": {"supported": False},
        "bulk": {"supported": False, "maxOperations": 0, "maxPayloadSize": 0},
        "filter": {"supported": True, "maxResults": 100},
        "changePassword": {"supported": False},
        "sort": {"supported": False},
        "etag": {"supported": False},
        "authenticationSchemes": [
            {
                "type": "oauthbearertoken",
                "name": "OAuth Bearer Token",
                "description": "JWT Bearer from MboaShield auth",
                "specUri": "http://www.rfc-editor.org/info/rfc6750",
                "primary": True,
            }
        ],
        "meta": {"resourceType": "ServiceProviderConfig", "location": "/scim/v2/ServiceProviderConfig"},
        "x_mboashield": {
            "mode": "read_and_create",
            "phase": "CI-1",
            "note": "POST /Users creates local accounts. PATCH/DELETE not enabled.",
        },
    }


@router.get("/Users")
def scim_list_users(
    startIndex: int = Query(1, ge=1),
    count: int = Query(50, ge=1, le=100),
    filter: str | None = None,
    _actor: Annotated[dict | None, Depends(require_permission("users:manage"))] = None,
):
    q = None
    if filter and "userName eq" in filter:
        parts = filter.split('"')
        if len(parts) >= 2:
            q = parts[1]
    users = list_users(q=q, limit=500)
    total = len(users)
    start = startIndex - 1
    end = start + count
    page = users[start:end]
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": total,
        "startIndex": startIndex,
        "itemsPerPage": len(page),
        "Resources": [_to_scim_user(item) for item in page],
    }


@router.get("/Users/{user_id}")
def scim_get_user(
    user_id: str,
    _actor: Annotated[dict | None, Depends(require_permission("users:manage"))] = None,
):
    users = list_users(limit=500)
    match = next((item for item in users if str(item["id"]) == str(user_id)), None)
    if not match:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_scim_user(match)


@router.post("/Users", status_code=201)
def scim_create_user(
    body: dict[str, Any],
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("users:manage"))] = None,
):
    user_name = (body.get("userName") or "").strip().lower()
    display_name = (body.get("displayName") or user_name or "SCIM User").strip()
    emails = body.get("emails") or []
    if not user_name and emails:
        user_name = str(emails[0].get("value") or "").strip().lower()
    if not user_name or "@" not in user_name:
        raise HTTPException(status_code=400, detail="userName (email) required")

    role = "citizen"
    roles = body.get("roles") or []
    if roles and isinstance(roles, list) and roles[0].get("value"):
        role = str(roles[0]["value"]).strip().lower()
    if role not in {"citizen", "analyst", "institution_admin", "admin"}:
        raise HTTPException(status_code=400, detail="Unsupported role for SCIM create")

    try:
        created = admin_create_user(
            display_name=display_name,
            email=user_name,
            role=role,
            password=None,
            invited_by_user_id=actor["id"] if actor else None,
            must_reset_password=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    write_audit_log(
        action="scim.user_create",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="user",
        resource_id=str(created["id"]),
        details={"email": user_name, "role": role},
        ip_address=request.client.host if request.client else None,
    )
    return _to_scim_user(created, include_temp_password=True)
