"""Institution Administration Portal APIs (Phase 10)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from ...core.config import get_settings
from ...institution_store import (
    add_domain,
    add_membership,
    add_official_account,
    assert_institution_portal_access,
    create_api_key,
    delete_official_account,
    get_branding,
    institution_analytics,
    list_api_keys,
    list_domains,
    list_investigations,
    list_memberships,
    list_official_accounts,
    portal_overview,
    revoke_api_key,
    update_branding,
    update_membership,
    verify_domain,
)
from ...repositories import list_institutions, write_audit_log
from ...schemas import (
    InstitutionApiKeyIn,
    InstitutionBrandingIn,
    InstitutionDomainIn,
    InstitutionDomainVerifyIn,
    InstitutionMembershipIn,
    InstitutionMembershipUpdateIn,
    InstitutionOfficialAccountIn,
)
from ..deps import require_permission

router = APIRouter(prefix="/institution-portal", tags=["institution-portal"])


def _ensure_portal():
    if not get_settings().institution_portal_enabled:
        raise HTTPException(status_code=404, detail="Institution portal is disabled")


def _actor_id(actor: dict | None) -> int | None:
    return actor["id"] if actor and actor.get("id") is not None else None


def _gate(actor: dict | None, institution_id: str, *, require_admin: bool = False) -> None:
    try:
        assert_institution_portal_access(actor, institution_id, require_admin=require_admin)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/health")
def api_portal_health():
    _ensure_portal()
    return {
        "enabled": True,
        "institutions_count": len(list_institutions()),
    }


@router.get("/{institution_id}/overview")
def api_overview(
    institution_id: str,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id)
    try:
        return portal_overview(institution_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{institution_id}/domains")
def api_list_domains(
    institution_id: str,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id)
    items = list_domains(institution_id)
    return {"domains": items, "count": len(items)}


@router.post("/{institution_id}/domains")
def api_add_domain(
    institution_id: str,
    body: InstitutionDomainIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id, require_admin=True)
    try:
        created = add_domain(
            institution_id,
            body.domain,
            verification_method=body.verification_method,
            created_by_user_id=_actor_id(actor),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="institution.domain_add",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="institution_domain",
        resource_id=str(created["id"]),
        details={"institution_id": institution_id, "domain": created["domain"]},
        ip_address=request.client.host if request.client else None,
    )
    return created


@router.post("/{institution_id}/domains/{domain_id}/verify")
def api_verify_domain(
    institution_id: str,
    domain_id: int,
    body: InstitutionDomainVerifyIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id, require_admin=True)
    try:
        verified = verify_domain(
            institution_id,
            domain_id,
            provided_token=body.token,
            force=body.force,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="institution.domain_verify",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="institution_domain",
        resource_id=str(domain_id),
        details={"institution_id": institution_id, "verified": verified.get("verified")},
        ip_address=request.client.host if request.client else None,
    )
    return verified


@router.get("/{institution_id}/memberships")
def api_list_memberships(
    institution_id: str,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id)
    items = list_memberships(institution_id)
    return {"memberships": items, "count": len(items)}


@router.post("/{institution_id}/memberships")
def api_add_membership(
    institution_id: str,
    body: InstitutionMembershipIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id, require_admin=True)
    try:
        created = add_membership(
            institution_id,
            user_id=body.user_id,
            email=body.email,
            display_name=body.display_name,
            member_role=body.member_role,
            invited_by_user_id=_actor_id(actor),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="institution.membership_add",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="institution_membership",
        resource_id=str(created["id"]),
        details={"institution_id": institution_id, "user_id": created["user_id"]},
        ip_address=request.client.host if request.client else None,
    )
    return created


@router.patch("/{institution_id}/memberships/{membership_id}")
def api_update_membership(
    institution_id: str,
    membership_id: int,
    body: InstitutionMembershipUpdateIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id, require_admin=True)
    try:
        updated = update_membership(
            institution_id,
            membership_id,
            member_role=body.member_role,
            status=body.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="institution.membership_update",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="institution_membership",
        resource_id=str(membership_id),
        details={"member_role": body.member_role, "status": body.status},
        ip_address=request.client.host if request.client else None,
    )
    return updated


@router.get("/{institution_id}/branding")
def api_get_branding(
    institution_id: str,
    actor: Annotated[dict | None, Depends(require_permission("institutions:read"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id)
    try:
        return get_branding(institution_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{institution_id}/branding")
def api_put_branding(
    institution_id: str,
    body: InstitutionBrandingIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id, require_admin=True)
    try:
        updated = update_branding(
            institution_id,
            branding=body.branding,
            contact_email=body.contact_email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="institution.branding_update",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="institution",
        resource_id=institution_id,
        ip_address=request.client.host if request.client else None,
    )
    return updated


@router.get("/{institution_id}/official-accounts")
def api_list_accounts(
    institution_id: str,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id)
    items = list_official_accounts(institution_id)
    return {"accounts": items, "count": len(items)}


@router.post("/{institution_id}/official-accounts")
def api_add_account(
    institution_id: str,
    body: InstitutionOfficialAccountIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id, require_admin=True)
    try:
        created = add_official_account(
            institution_id,
            platform=body.platform,
            handle=body.handle,
            url=body.url,
            verified=body.verified,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="institution.official_account_add",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="institution_official_account",
        resource_id=str(created["id"]),
        details={"platform": created["platform"], "handle": created["handle"]},
        ip_address=request.client.host if request.client else None,
    )
    return created


@router.delete("/{institution_id}/official-accounts/{account_id}")
def api_delete_account(
    institution_id: str,
    account_id: int,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id, require_admin=True)
    if not delete_official_account(institution_id, account_id):
        raise HTTPException(status_code=404, detail="Official account not found")
    write_audit_log(
        action="institution.official_account_delete",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="institution_official_account",
        resource_id=str(account_id),
        ip_address=request.client.host if request.client else None,
    )
    return {"deleted": True, "id": account_id}


@router.get("/{institution_id}/api-keys")
def api_list_keys(
    institution_id: str,
    include_revoked: bool = False,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id, require_admin=True)
    items = list_api_keys(institution_id, include_revoked=include_revoked)
    return {"keys": items, "count": len(items)}


@router.post("/{institution_id}/api-keys")
def api_create_key(
    institution_id: str,
    body: InstitutionApiKeyIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id, require_admin=True)
    try:
        created = create_api_key(
            institution_id,
            name=body.name,
            scopes=body.scopes,
            created_by_user_id=_actor_id(actor),
            expires_at=body.expires_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="institution.api_key_create",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="institution_api_key",
        resource_id=str(created["id"]),
        details={"scopes": created.get("scopes")},
        ip_address=request.client.host if request.client else None,
    )
    return created


@router.delete("/{institution_id}/api-keys/{key_id}")
def api_revoke_key(
    institution_id: str,
    key_id: int,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id, require_admin=True)
    row = revoke_api_key(institution_id, key_id)
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    write_audit_log(
        action="institution.api_key_revoke",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="institution_api_key",
        resource_id=str(key_id),
        ip_address=request.client.host if request.client else None,
    )
    return row


@router.get("/{institution_id}/investigations")
def api_investigations(
    institution_id: str,
    limit: int = 50,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id)
    items = list_investigations(institution_id, limit=limit)
    return {"cases": items, "count": len(items)}


@router.get("/{institution_id}/analytics")
def api_analytics(
    institution_id: str,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    _ensure_portal()
    _gate(actor, institution_id)
    return institution_analytics(institution_id)
