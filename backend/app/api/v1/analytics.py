"""National analytics API for government situational awareness."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from ...schemas import AnalysisFeedbackIn, AnalysisFeedbackOut
from ...services.analytics import build_national_analytics, record_analysis_feedback
from ...repositories import write_audit_log
from ..deps import require_permission

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/national")
def api_national_analytics(
    _actor: Annotated[dict | None, Depends(require_permission("history:read_all"))] = None,
):
    return build_national_analytics()


@router.get("/threats")
def api_threat_analytics(
    _actor: Annotated[dict | None, Depends(require_permission("history:read_all"))] = None,
):
    data = build_national_analytics()
    return {
        "threat_trends": data["threat_trends"],
        "deepfake_trends": data["deepfake_trends"],
        "institution_attacks": data["institution_attacks"],
        "generated_at": data["generated_at"],
    }


@router.get("/regions")
def api_regional_analytics(
    _actor: Annotated[dict | None, Depends(require_permission("history:read_all"))] = None,
):
    data = build_national_analytics()
    return {
        "regional_heat_map": data["regional_heat_map"],
        "generated_at": data["generated_at"],
    }


@router.get("/incidents/timeline")
def api_incident_timeline_analytics(
    _actor: Annotated[dict | None, Depends(require_permission("history:read_all"))] = None,
):
    data = build_national_analytics()
    return {
        "incident_timeline": data["incident_timeline"],
        "response_time": data["response_time"],
        "generated_at": data["generated_at"],
    }


@router.get("/performance")
def api_performance_analytics(
    _actor: Annotated[dict | None, Depends(require_permission("history:read_all"))] = None,
):
    data = build_national_analytics()
    return {
        "response_time": data["response_time"],
        "ai_accuracy": data["ai_accuracy"],
        "generated_at": data["generated_at"],
    }


@router.get("/participation")
def api_participation_analytics(
    _actor: Annotated[dict | None, Depends(require_permission("history:read_all"))] = None,
):
    data = build_national_analytics()
    return {
        "citizen_participation": data["citizen_participation"],
        "overview": data["overview"],
        "generated_at": data["generated_at"],
    }


@router.post("/feedback", response_model=AnalysisFeedbackOut)
def api_analysis_feedback(
    body: AnalysisFeedbackIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    try:
        row = record_analysis_feedback(
            check_id=body.verification_check_id,
            label=body.label,
            note=body.note,
            actor_user_id=actor["id"] if actor else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="analytics.feedback",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="verification_check",
        resource_id=str(body.verification_check_id),
        details={"label": body.label},
        ip_address=request.client.host if request.client else None,
    )
    return row
