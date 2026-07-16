"""Government workflow, analyst, citizen, and institution-admin endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from ...repositories import (
    get_incident_report,
    get_institution,
    get_user,
    incident_status_counts,
    list_incident_events,
    list_incident_reports,
    list_institutions,
    list_recent_certificates,
    list_verification_checks_for_user,
    update_incident_status,
    upsert_institution,
    write_audit_log,
)
from ...schemas import (
    IncidentReportOut,
    IncidentReportsOut,
    IncidentTimelineOut,
    IncidentTransitionIn,
    InstitutionIn,
    InstitutionOut,
    InstitutionUpdateIn,
)
from ...services.incident_workflow import workflow_blueprint
from ..deps import LegacyUserId, require_permission

router = APIRouter(tags=["government"])


@router.get("/workflow/states")
def api_workflow_states():
    return workflow_blueprint()


@router.post("/incidents/{report_id}/transition", response_model=IncidentReportOut)
def api_transition_incident(
    report_id: int,
    body: IncidentTransitionIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    try:
        report = update_incident_status(
            report_id,
            status=body.to_status,
            reviewer_note=body.note,
            actor_user_id=actor["id"] if actor else None,
            actor_role=actor["role"] if actor else None,
            decision_summary=body.decision_summary,
            public_advisory=body.public_advisory,
            assigned_to_user_id=body.assigned_to_user_id,
            institution_id=body.institution_id,
            region=body.region,
            priority=body.priority,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not report:
        raise HTTPException(status_code=404, detail="Incident report not found")
    write_audit_log(
        action="incident.transition",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="incident",
        resource_id=str(report_id),
        details={"to_status": body.to_status},
        ip_address=request.client.host if request.client else None,
    )
    try:
        from ...services.notifications import notify_incident_transition

        notify_incident_transition(
            incident_id=report_id,
            to_status=body.to_status,
            actor_user_id=actor["id"] if actor else None,
        )
    except Exception:
        pass
    return report


@router.get("/incidents/{report_id}/timeline", response_model=IncidentTimelineOut)
def api_incident_timeline(report_id: int):
    if not get_incident_report(report_id):
        raise HTTPException(status_code=404, detail="Incident report not found")
    events = list_incident_events(report_id)
    return {"incident_id": report_id, "events": events, "count": len(events)}


@router.get("/analyst/queue", response_model=IncidentReportsOut)
def api_analyst_queue(
    limit: int = 30,
    _actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    reports = list_incident_reports(
        limit=limit,
        statuses=["open", "ai_analysis", "analyst_review", "reviewing", "institution_review", "decision"],
    )
    return {"reports": reports, "count": len(reports)}


@router.get("/analyst/summary")
def api_analyst_summary(
    _actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    counts = incident_status_counts()
    return {
        "status_counts": counts,
        "queue_total": sum(
            counts.get(key, 0)
            for key in ("open", "ai_analysis", "analyst_review", "reviewing", "institution_review", "decision")
        ),
        "workflow": workflow_blueprint()["pipeline"],
    }


@router.get("/citizen/dashboard")
def api_citizen_dashboard(user_id: LegacyUserId, limit: int = 20):
    if user_id is None:
        raise HTTPException(
            status_code=400,
            detail="Provide X-MboaShield-User-Id header or authenticate to load citizen dashboard",
        )
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    checks = list_verification_checks_for_user(user_id, limit=limit)
    reports = list_incident_reports(limit=limit, user_id=user_id)
    certificates = [
        cert
        for cert in list_recent_certificates(limit=100)
        if cert.get("learner_name", "").lower() == (user.get("display_name") or "").lower()
    ][:limit]
    return {
        "user": user,
        "checks": checks,
        "checks_count": len(checks),
        "incidents": reports,
        "incidents_count": len(reports),
        "certificates": certificates,
        "certificates_count": len(certificates),
    }


@router.post("/institutions", response_model=InstitutionOut)
def api_create_institution(
    body: InstitutionIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    if get_institution(body.id):
        raise HTTPException(status_code=409, detail="Institution already exists")
    try:
        institution = upsert_institution(
            institution_id=body.id,
            name=body.name,
            short_name=body.short_name,
            url=body.url,
            verified=body.verified,
            handles=body.handles,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="institution.create",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="institution",
        resource_id=body.id,
        ip_address=request.client.host if request.client else None,
    )
    return institution


@router.patch("/institutions/{institution_id}", response_model=InstitutionOut)
def api_update_institution(
    institution_id: str,
    body: InstitutionUpdateIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    existing = get_institution(institution_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Institution not found")
    try:
        institution = upsert_institution(
            institution_id=institution_id,
            name=body.name if body.name is not None else existing["name"],
            short_name=body.short_name if body.short_name is not None else existing["short_name"],
            url=body.url if body.url is not None else existing.get("url"),
            verified=body.verified if body.verified is not None else existing.get("verified", True),
            handles=body.handles if body.handles is not None else existing.get("handles", []),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="institution.update",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="institution",
        resource_id=institution_id,
        ip_address=request.client.host if request.client else None,
    )
    return institution


@router.get("/institutions-admin/overview")
def api_institutions_admin_overview(
    _actor: Annotated[dict | None, Depends(require_permission("institutions:manage"))] = None,
):
    institutions = list_institutions()
    return {
        "institutions": institutions,
        "count": len(institutions),
        "verified_count": sum(1 for item in institutions if item.get("verified")),
    }
