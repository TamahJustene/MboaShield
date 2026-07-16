"""Threat intelligence APIs - compliant sources only."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse

from ...core.config import get_settings
from ...intel_store import (
    build_national_intel_report,
    correlate_intel,
    create_intel_source,
    get_intel_source,
    ingest_source,
    ingest_webhook,
    list_campaigns,
    list_correlations,
    list_intel_items,
    list_intel_sources,
    set_intel_source_enabled,
)
from ...repositories import write_audit_log
from ...schemas import IntelSourceIn, IntelSourceUpdateIn
from ...services.intel.connectors import ALLOWED_SOURCE_CLASSES
from ..deps import require_permission

router = APIRouter(prefix="/intel", tags=["intel"])


def _ensure_intel():
    if not get_settings().intel_enabled:
        raise HTTPException(status_code=404, detail="Threat intelligence is disabled")


@router.get("/source-classes")
def api_source_classes():
    _ensure_intel()
    return {
        "allowed": sorted(ALLOWED_SOURCE_CLASSES),
        "forbidden": ["html_scrape", "browser_scrape", "credential_stuffing", "tos_bypass"],
        "policy": "Only official APIs, RSS/Atom, open data, and partner webhooks are permitted.",
    }


@router.get("/sources")
def api_list_sources(
    enabled_only: bool = False,
    _actor: Annotated[dict | None, Depends(require_permission("intel:read"))] = None,
):
    _ensure_intel()
    items = list_intel_sources(enabled_only=enabled_only)
    return {"sources": items, "count": len(items)}


@router.post("/sources")
def api_create_source(
    body: IntelSourceIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("intel:manage"))] = None,
):
    _ensure_intel()
    try:
        created = create_intel_source(
            name=body.name,
            source_class=body.source_class,
            endpoint_url=body.endpoint_url,
            tos_reference=body.tos_reference,
            license_name=body.license,
            auth_type=body.auth_type,
            credentials=body.credentials,
            config=body.config,
            enabled=body.enabled,
            created_by_user_id=actor["id"] if actor else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="intel.source_create",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="intel_source",
        resource_id=str(created["id"]),
        details={"source_class": created["source_class"], "egress_host": created["egress_host"]},
        ip_address=request.client.host if request.client else None,
    )
    return created


@router.patch("/sources/{source_id}")
def api_patch_source(
    source_id: int,
    body: IntelSourceUpdateIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("intel:manage"))] = None,
):
    _ensure_intel()
    if body.enabled is None:
        raise HTTPException(status_code=400, detail="enabled is required")
    try:
        updated = set_intel_source_enabled(source_id, body.enabled)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    write_audit_log(
        action="intel.source_update",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="intel_source",
        resource_id=str(source_id),
        details={"enabled": body.enabled},
        ip_address=request.client.host if request.client else None,
    )
    return updated


@router.post("/sources/{source_id}/ingest")
def api_ingest_source(
    source_id: int,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("intel:manage"))] = None,
):
    _ensure_intel()
    try:
        result = ingest_source(source_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # network/parse errors
        raise HTTPException(status_code=502, detail=f"Ingest failed: {exc}") from exc
    write_audit_log(
        action="intel.ingest",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="intel_source",
        resource_id=str(source_id),
        details=result,
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.post("/webhook/{source_id}")
def api_webhook_ingest(
    source_id: int,
    payload: dict[str, Any],
    request: Request,
):
    """Partner push webhook - no scraping. Soft-open when AUTH_ENFORCE=false."""
    _ensure_intel()
    source = get_intel_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    try:
        result = ingest_webhook(source_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="intel.webhook",
        resource_type="intel_source",
        resource_id=str(source_id),
        details={"created": result.get("created")},
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/items")
def api_list_items(
    source_id: int | None = None,
    q: str | None = None,
    limit: int = 50,
    _actor: Annotated[dict | None, Depends(require_permission("intel:read"))] = None,
):
    _ensure_intel()
    items = list_intel_items(source_id=source_id, q=q, limit=limit)
    return {"items": items, "count": len(items)}


@router.post("/correlate")
def api_correlate(
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("intel:manage"))] = None,
):
    _ensure_intel()
    result = correlate_intel()
    write_audit_log(
        action="intel.correlate",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="intel",
        details=result,
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/campaigns")
def api_campaigns(
    limit: int = 50,
    _actor: Annotated[dict | None, Depends(require_permission("intel:read"))] = None,
):
    _ensure_intel()
    items = list_campaigns(limit=limit)
    return {"campaigns": items, "count": len(items)}


@router.get("/correlations")
def api_correlations(
    limit: int = 50,
    _actor: Annotated[dict | None, Depends(require_permission("intel:read"))] = None,
):
    _ensure_intel()
    items = list_correlations(limit=limit)
    return {"correlations": items, "count": len(items)}


@router.get("/reports/national")
def api_national_report(
    format: str = "json",
    _actor: Annotated[dict | None, Depends(require_permission("intel:read"))] = None,
):
    _ensure_intel()
    report = build_national_intel_report()
    if format == "markdown":
        return PlainTextResponse(report["markdown"], media_type="text/markdown; charset=utf-8")
    return report
