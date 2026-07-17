"""Interoperability APIs - webhooks, STIX, CAP, CSV (T4)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ...core.config import get_settings
from ...core.openapi_pillars import PILLAR_PARTNER
from ...interop_store import (
    create_webhook_endpoint,
    list_deliveries,
    list_webhook_endpoints,
    set_webhook_endpoint_enabled,
)
from ...repositories import write_audit_log
from ...schemas import WebhookEndpointIn, WebhookEmitIn
from ...services.interop.cap_export import export_cap_bundle, export_cap_for_incident
from ...services.interop.reports import incidents_csv
from ...services.interop.stix_export import build_stix_bundle
from ...services.interop.webhooks import emit_event, event_catalog
from ..deps import require_permission

router = APIRouter(prefix="/interop", tags=[PILLAR_PARTNER])


@router.get("/status")
def api_interop_status():
    settings = get_settings()
    return {
        "enabled": settings.interop_enabled,
        "version": settings.version,
        "transformation_phase": "T4",
        "features": {
            "webhooks": True,
            "stix_export": True,
            "cap_export": True,
            "csv_reports": True,
            "taxii_server": False,
        },
        "events": event_catalog(),
    }


@router.get("/events")
def api_event_catalog():
    return {"events": event_catalog(), "count": len(event_catalog())}


@router.get("/webhooks")
def api_list_webhooks(
    _actor: Annotated[dict | None, Depends(require_permission("partners:manage"))] = None,
):
    items = list_webhook_endpoints()
    return {"endpoints": items, "count": len(items)}


@router.post("/webhooks")
def api_create_webhook(
    body: WebhookEndpointIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("partners:manage"))] = None,
):
    try:
        created = create_webhook_endpoint(
            name=body.name,
            url=body.url,
            events=body.events,
            partner_org=body.partner_org,
            secret=body.secret,
            enabled=body.enabled,
            created_by_user_id=actor["id"] if actor else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="interop.webhook_create",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="webhook_endpoint",
        resource_id=str(created["id"]),
        details={"url": body.url, "events": body.events},
        ip_address=request.client.host if request.client else None,
    )
    return created


@router.patch("/webhooks/{endpoint_id}")
def api_toggle_webhook(
    endpoint_id: int,
    enabled: bool,
    actor: Annotated[dict | None, Depends(require_permission("partners:manage"))] = None,
):
    row = set_webhook_endpoint_enabled(endpoint_id, enabled=enabled)
    if not row:
        raise HTTPException(status_code=404, detail="Webhook endpoint not found")
    return row


@router.get("/webhooks/deliveries")
def api_list_deliveries(
    endpoint_id: int | None = None,
    limit: int = 50,
    _actor: Annotated[dict | None, Depends(require_permission("partners:manage"))] = None,
):
    items = list_deliveries(endpoint_id=endpoint_id, limit=limit)
    return {"deliveries": items, "count": len(items)}


@router.post("/webhooks/emit")
def api_emit_event(
    body: WebhookEmitIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("partners:manage"))] = None,
):
    result = emit_event(body.event_type, body.data or {}, sync_deliver=body.sync_deliver)
    write_audit_log(
        action="interop.webhook_emit",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="webhook_event",
        resource_id=result["event"]["id"],
        details={"event_type": body.event_type, "deliveries": result["count"]},
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/stix/bundle")
def api_stix_bundle(limit: int = 50, q: str | None = None):
    if not get_settings().interop_enabled:
        raise HTTPException(status_code=404, detail="Interop disabled")
    return build_stix_bundle(limit=limit, query=q)


@router.get("/cap/incident/{incident_id}")
def api_cap_incident(incident_id: int):
    try:
        xml = export_cap_for_incident(incident_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(content=xml, media_type="application/xml")


@router.get("/cap/bundle")
def api_cap_bundle(limit: int = 20):
    return export_cap_bundle(limit=limit)


@router.get("/reports/incidents.csv")
def api_incidents_csv(limit: int = 200, status: str | None = None):
    content = incidents_csv(limit=limit, status=status)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=mboashield-incidents.csv"},
    )
