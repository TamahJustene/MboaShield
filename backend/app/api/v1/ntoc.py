"""NTOC dashboard and notifications APIs."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ...core.config import get_settings
from ...ntoc_store import list_notifications, mark_notification_read
from ...services.ntoc import (
    build_ntoc_dashboard,
    build_regional_map,
    compute_institution_health,
    compute_threat_level,
)
from ..deps import require_permission

router = APIRouter(tags=["ntoc"])


def _ensure_ntoc():
    if not get_settings().ntoc_enabled:
        raise HTTPException(status_code=404, detail="NTOC is disabled")


@router.get("/ntoc/threat-level")
def api_threat_level(
    _actor: Annotated[dict | None, Depends(require_permission("history:read_all"))] = None,
):
    _ensure_ntoc()
    return compute_threat_level()


@router.get("/ntoc/dashboard")
def api_ntoc_dashboard(
    _actor: Annotated[dict | None, Depends(require_permission("history:read_all"))] = None,
):
    _ensure_ntoc()
    return build_ntoc_dashboard()


@router.get("/ntoc/regions")
def api_ntoc_regions(
    _actor: Annotated[dict | None, Depends(require_permission("history:read_all"))] = None,
):
    _ensure_ntoc()
    return build_regional_map()


@router.get("/ntoc/institution-health")
def api_institution_health(
    _actor: Annotated[dict | None, Depends(require_permission("history:read_all"))] = None,
):
    _ensure_ntoc()
    items = compute_institution_health()
    return {"institutions": items, "count": len(items)}


@router.get("/notifications")
def api_list_notifications(
    audience: str = "analyst",
    unread_only: bool = False,
    limit: int = 50,
    actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    _ensure_ntoc()
    user_id = actor["id"] if actor else None
    items = list_notifications(audience=audience, user_id=user_id, unread_only=unread_only, limit=limit)
    return {"notifications": items, "count": len(items), "unread": sum(1 for item in items if not item["read"])}


@router.post("/notifications/{notification_id}/read")
def api_mark_read(
    notification_id: int,
    _actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    _ensure_ntoc()
    item = mark_notification_read(notification_id)
    if not item:
        raise HTTPException(status_code=404, detail="Notification not found")
    return item
