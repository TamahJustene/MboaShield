"""SCIM 2.0 read-only Users stub (MboaShield 2030 T5)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from ...core.openapi_pillars import PILLAR_IDENTITY
from ...identity_store import list_users
from ..deps import require_permission

router = APIRouter(prefix="/scim/v2", tags=[PILLAR_IDENTITY])


def _to_scim_user(user: dict) -> dict:
    return {
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
            "mode": "read_only_stub",
            "phase": "T5",
            "note": "User provisioning writes are not enabled in this release.",
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
        # minimal filter parse: userName eq "email"
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


@router.post("/Users")
def scim_create_user_not_implemented():
    raise HTTPException(
        status_code=501,
        detail="SCIM write provisioning is not enabled (T5 read-only stub)",
    )
