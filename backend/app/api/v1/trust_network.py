"""National Digital Trust Network API (MboaShield 2030 T2)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from ...core.openapi_pillars import PILLAR_PARTNER
from ...repositories import write_audit_log
from ...schemas import (
    ExchangeChannelIn,
    SharedAlertIn,
    TrustRelationshipIn,
    TrustRelationshipStatusIn,
)
from ...trust_network_store import (
    create_channel,
    create_relationship,
    create_shared_alert,
    get_relationship,
    get_shared_alert,
    list_channels,
    list_relationships,
    list_shared_alerts,
    network_status,
    update_relationship_status,
)
from ..deps import require_permission

router = APIRouter(prefix="/trust-network", tags=[PILLAR_PARTNER])


@router.get("/status")
def api_network_status():
    return network_status()


@router.get("/relationships")
def api_list_relationships(
    institution_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
):
    items = list_relationships(institution_id=institution_id, status=status, limit=limit)
    return {"relationships": items, "count": len(items)}


@router.post("/relationships")
def api_create_relationship(
    body: TrustRelationshipIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    try:
        row = create_relationship(
            source_institution_id=body.source_institution_id,
            target_institution_id=body.target_institution_id,
            status=body.status,
            policy_note=body.policy_note or "",
            created_by_user_id=actor["id"] if actor else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="trust_network.relationship_create",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="trust_relationship",
        resource_id=str(row["id"]),
        details={
            "source": body.source_institution_id,
            "target": body.target_institution_id,
            "status": body.status,
        },
        ip_address=request.client.host if request.client else None,
    )
    return row


@router.get("/relationships/{relationship_id}")
def api_get_relationship(relationship_id: int):
    row = get_relationship(relationship_id)
    if not row:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return row


@router.patch("/relationships/{relationship_id}")
def api_update_relationship(
    relationship_id: int,
    body: TrustRelationshipStatusIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    try:
        row = update_relationship_status(
            relationship_id,
            status=body.status,
            policy_note=body.policy_note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not row:
        raise HTTPException(status_code=404, detail="Relationship not found")
    write_audit_log(
        action="trust_network.relationship_update",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="trust_relationship",
        resource_id=str(relationship_id),
        details={"status": body.status},
        ip_address=request.client.host if request.client else None,
    )
    return row


@router.get("/exchange/channels")
def api_list_channels(relationship_id: int | None = None, limit: int = 50):
    items = list_channels(relationship_id=relationship_id, limit=limit)
    return {"channels": items, "count": len(items)}


@router.post("/exchange/channels")
def api_create_channel(
    body: ExchangeChannelIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    try:
        row = create_channel(
            relationship_id=body.relationship_id,
            channel_type=body.channel_type,
            label=body.label or "",
            enabled=body.enabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="trust_network.channel_create",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="exchange_channel",
        resource_id=str(row["id"]),
        details={"relationship_id": body.relationship_id, "channel_type": body.channel_type},
        ip_address=request.client.host if request.client else None,
    )
    return row


@router.get("/exchange/alerts")
def api_list_alerts(
    institution_id: str | None = None,
    alert_type: str | None = None,
    limit: int = 50,
):
    items = list_shared_alerts(
        institution_id=institution_id, alert_type=alert_type, limit=limit
    )
    return {"alerts": items, "count": len(items)}


@router.post("/exchange/alerts")
def api_create_alert(
    body: SharedAlertIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    try:
        row = create_shared_alert(
            alert_type=body.alert_type,
            title=body.title,
            summary=body.summary or "",
            severity=body.severity,
            source_institution_id=body.source_institution_id,
            target_institutions=body.target_institutions,
            relationship_id=body.relationship_id,
            verification_check_id=body.verification_check_id,
            trust_assessment_id=body.trust_assessment_id,
            payload=body.payload,
            created_by_user_id=actor["id"] if actor else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="trust_network.alert_share",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="shared_alert",
        resource_id=str(row["id"]),
        details={
            "alert_type": body.alert_type,
            "source": body.source_institution_id,
            "targets": body.target_institutions,
        },
        ip_address=request.client.host if request.client else None,
    )
    return row


@router.get("/exchange/alerts/{alert_id}")
def api_get_alert(alert_id: int):
    row = get_shared_alert(alert_id)
    if not row:
        raise HTTPException(status_code=404, detail="Shared alert not found")
    return row
