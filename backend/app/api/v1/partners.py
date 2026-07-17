"""Partner API key management."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from ...repositories import (
    create_partner_api_key,
    list_partner_api_keys,
    revoke_partner_api_key,
    write_audit_log,
)
from ...schemas import PartnerApiKeyIn, PartnerApiKeyOut
from ..deps import get_optional_api_key_actor, require_permission

router = APIRouter(prefix="/partners", tags=["pillar-partner"])


@router.post("/keys", response_model=PartnerApiKeyOut)
def api_create_partner_key(
    body: PartnerApiKeyIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("partners:manage"))] = None,
):
    try:
        created = create_partner_api_key(
            name=body.name,
            partner_org=body.partner_org,
            scopes=body.scopes,
            created_by_user_id=actor["id"] if actor and actor.get("auth_type") != "api_key" else None,
            expires_at=body.expires_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="partners.api_key_create",
        actor_user_id=actor.get("id") if actor else None,
        actor_role=actor.get("role") if actor else None,
        resource_type="partner_api_key",
        resource_id=str(created["id"]),
        details={"partner_org": body.partner_org, "scopes": body.scopes},
        ip_address=request.client.host if request.client else None,
    )
    return created


@router.get("/keys", response_model=list[PartnerApiKeyOut])
def api_list_partner_keys(
    include_revoked: bool = False,
    _actor: Annotated[dict | None, Depends(require_permission("partners:manage"))] = None,
):
    return list_partner_api_keys(include_revoked=include_revoked)


@router.delete("/keys/{key_id}", response_model=PartnerApiKeyOut)
def api_revoke_partner_key(
    key_id: int,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("partners:manage"))] = None,
):
    row = revoke_partner_api_key(key_id)
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    write_audit_log(
        action="partners.api_key_revoke",
        actor_user_id=actor.get("id") if actor else None,
        actor_role=actor.get("role") if actor else None,
        resource_type="partner_api_key",
        resource_id=str(key_id),
        ip_address=request.client.host if request.client else None,
    )
    return row


@router.get("/me")
def api_partner_me(actor: Annotated[dict | None, Depends(get_optional_api_key_actor)] = None):
    if not actor:
        raise HTTPException(status_code=401, detail="Valid X-API-Key required")
    return actor
