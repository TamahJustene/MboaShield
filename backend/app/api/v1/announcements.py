"""Verified government announcement lifecycle APIs."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse

from ...announcement_store import (
    build_certificate,
    build_qr_payload,
    certificate_markdown,
    create_announcement_draft,
    get_announcement_detail,
    list_announcements,
    publish_announcement,
    revoke_announcement,
    update_draft,
    verify_announcement,
)
from ...core.config import get_settings
from ...repositories import write_audit_log
from ...schemas import AnnouncementCreateIn, AnnouncementPublishIn, AnnouncementUpdateIn
from ..deps import require_permission

router = APIRouter(prefix="/announcements", tags=["pillar-comms"])


def _ensure_comms():
    if not get_settings().verified_comms_enabled:
        raise HTTPException(status_code=404, detail="Verified communications are disabled")


def _actor_id(actor: dict | None) -> int | None:
    return actor["id"] if actor and actor.get("id") is not None else None


@router.get("/health")
def api_comms_health():
    _ensure_comms()
    return {"enabled": True, "signing_kid": get_settings().announcement_signing_kid}


@router.get("")
def api_list(
    institution_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    _actor: Annotated[dict | None, Depends(require_permission("announcements:read"))] = None,
):
    _ensure_comms()
    items = list_announcements(institution_id=institution_id, status=status, limit=limit)
    return {"announcements": items, "count": len(items)}


@router.post("")
def api_create(
    body: AnnouncementCreateIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("announcements:publish"))] = None,
):
    _ensure_comms()
    try:
        created = create_announcement_draft(
            institution_id=body.institution_id,
            title=body.title,
            body=body.body,
            locale=body.locale,
            created_by_user_id=_actor_id(actor),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="announcement.create",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="announcement",
        resource_id=created["announcement_id"],
        details={"institution_id": body.institution_id},
        ip_address=request.client.host if request.client else None,
    )
    return get_announcement_detail(created["announcement_id"])


@router.get("/{announcement_id}")
def api_get(
    announcement_id: str,
    _actor: Annotated[dict | None, Depends(require_permission("announcements:read"))] = None,
):
    _ensure_comms()
    detail = get_announcement_detail(announcement_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return detail


@router.patch("/{announcement_id}")
def api_update(
    announcement_id: str,
    body: AnnouncementUpdateIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("announcements:publish"))] = None,
):
    _ensure_comms()
    try:
        updated = update_draft(
            announcement_id,
            title=body.title,
            body=body.body,
            locale=body.locale,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="announcement.update",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="announcement",
        resource_id=announcement_id,
        ip_address=request.client.host if request.client else None,
    )
    return get_announcement_detail(updated["announcement_id"])


@router.post("/{announcement_id}/publish")
def api_publish(
    announcement_id: str,
    body: AnnouncementPublishIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("announcements:publish"))] = None,
):
    _ensure_comms()
    try:
        published = publish_announcement(
            announcement_id,
            published_by_user_id=_actor_id(actor),
            title=body.title,
            body=body.body,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="announcement.publish",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="announcement",
        resource_id=announcement_id,
        details={"version": published.get("version", {}).get("version_number")},
        ip_address=request.client.host if request.client else None,
    )
    return published


@router.post("/{announcement_id}/revoke")
def api_revoke(
    announcement_id: str,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("announcements:publish"))] = None,
):
    _ensure_comms()
    try:
        revoked = revoke_announcement(announcement_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="announcement.revoke",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="announcement",
        resource_id=announcement_id,
        ip_address=request.client.host if request.client else None,
    )
    return revoked


@router.get("/{announcement_id}/verify")
def api_verify_managed(
    announcement_id: str,
    version: int | None = None,
    _actor: Annotated[dict | None, Depends(require_permission("announcements:read"))] = None,
):
    _ensure_comms()
    try:
        return verify_announcement(announcement_id, version_number=version)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{announcement_id}/qr")
def api_qr(
    announcement_id: str,
    version: int | None = None,
    _actor: Annotated[dict | None, Depends(require_permission("announcements:read"))] = None,
):
    _ensure_comms()
    try:
        return build_qr_payload(announcement_id, version_number=version)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{announcement_id}/certificate")
def api_certificate(
    announcement_id: str,
    version: int | None = None,
    format: str = "json",
    _actor: Annotated[dict | None, Depends(require_permission("announcements:read"))] = None,
):
    _ensure_comms()
    try:
        cert = build_certificate(announcement_id, version_number=version)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if format == "markdown":
        return PlainTextResponse(certificate_markdown(cert), media_type="text/markdown")
    return cert
