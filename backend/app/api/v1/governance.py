"""Governance APIs: consent, risk register, cards, compliance (Phase 14)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from ...core.config import get_settings
from ...governance_store import (
    compliance_dashboard,
    ensure_governance_seed,
    framework_map,
    list_consents,
    list_controls,
    list_dataset_cards,
    list_model_cards,
    list_optional_features,
    list_risks,
    update_risk,
    upsert_consent,
)
from ...repositories import write_audit_log
from ...schemas import ConsentIn, RiskUpdateIn
from ..deps import require_permission

router = APIRouter(prefix="/governance", tags=["pillar-governance"])


def _ensure_gov() -> None:
    if not get_settings().governance_enabled:
        raise HTTPException(status_code=404, detail="Governance module is disabled")


def _actor_id(actor: dict | None) -> int | None:
    return actor["id"] if actor and actor.get("id") is not None else None


@router.get("/health")
def api_governance_health():
    _ensure_gov()
    ensure_governance_seed()
    return {
        "enabled": True,
        "features": list_optional_features(),
        "risks": len(list_risks()),
        "controls": len(list_controls()),
        "model_cards": len(list_model_cards()),
        "dataset_cards": len(list_dataset_cards()),
        "certainty_policy": "none",
    }


@router.get("/features")
def api_list_features():
    _ensure_gov()
    return {"items": list_optional_features()}


@router.post("/consent")
def api_upsert_consent(
    body: ConsentIn,
    actor: Annotated[dict | None, Depends(require_permission("consent:write"))] = None,
):
    _ensure_gov()
    subject = (body.subject_key or "").strip()
    if not subject and actor and actor.get("id") is not None:
        subject = f"user:{actor['id']}"
    if not subject:
        raise HTTPException(status_code=400, detail="subject_key required")
    try:
        record = upsert_consent(
            subject_key=subject,
            feature=body.feature,
            granted=body.granted,
            user_id=_actor_id(actor),
            purpose=body.purpose,
            policy_version=body.policy_version,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="governance.consent",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="consent",
        resource_id=f"{subject}:{body.feature}",
        details={"granted": body.granted, "feature": body.feature},
    )
    return record


@router.get("/consent")
def api_list_consent(
    subject_key: str | None = None,
    _actor: Annotated[dict | None, Depends(require_permission("governance:read"))] = None,
):
    _ensure_gov()
    return {"items": list_consents(subject_key=subject_key)}


@router.get("/risks")
def api_list_risks(
    status: str | None = None,
    _actor: Annotated[dict | None, Depends(require_permission("governance:read"))] = None,
):
    _ensure_gov()
    ensure_governance_seed()
    return {"items": list_risks(status=status)}


@router.patch("/risks/{risk_id}")
def api_update_risk(
    risk_id: str,
    body: RiskUpdateIn,
    actor: Annotated[dict | None, Depends(require_permission("governance:manage"))] = None,
):
    _ensure_gov()
    try:
        item = update_risk(
            risk_id,
            status=body.status,
            mitigation=body.mitigation,
            residual_risk=body.residual_risk,
            owner=body.owner,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    write_audit_log(
        action="governance.risk_update",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="risk_register",
        resource_id=risk_id,
        details=body.model_dump(exclude_none=True),
    )
    return item


@router.get("/model-cards")
def api_model_cards(
    _actor: Annotated[dict | None, Depends(require_permission("governance:read"))] = None,
):
    _ensure_gov()
    ensure_governance_seed()
    return {"items": list_model_cards()}


@router.get("/dataset-cards")
def api_dataset_cards(
    _actor: Annotated[dict | None, Depends(require_permission("governance:read"))] = None,
):
    _ensure_gov()
    ensure_governance_seed()
    return {"items": list_dataset_cards()}


@router.get("/controls")
def api_controls(
    _actor: Annotated[dict | None, Depends(require_permission("governance:read"))] = None,
):
    _ensure_gov()
    ensure_governance_seed()
    return {"items": list_controls()}


@router.get("/framework-map")
def api_framework_map(
    _actor: Annotated[dict | None, Depends(require_permission("governance:read"))] = None,
):
    """ISO/NIST assessable mappings for governance controls (T7 - not certification)."""
    _ensure_gov()
    ensure_governance_seed()
    return framework_map()


@router.get("/compliance")
def api_compliance(
    _actor: Annotated[dict | None, Depends(require_permission("governance:read"))] = None,
):
    _ensure_gov()
    ensure_governance_seed()
    return compliance_dashboard()
