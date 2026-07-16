"""Investigation cases API (Phase 7 NTOC)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from ...ntoc_store import (
    add_case_note,
    create_case,
    evidence_for_case,
    get_case,
    list_case_assignments,
    list_case_notes,
    search_cases,
    update_case,
)
from ...repositories import write_audit_log
from ...schemas import CaseAssignIn, CaseCreateIn, CaseNoteIn, CaseUpdateIn
from ...services.notifications import notify_case_assignment
from ...services.ntoc import build_investigation_workspace
from ..deps import require_permission

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("")
def api_list_cases(
    q: str | None = None,
    status: str | None = None,
    assigned_to_user_id: int | None = None,
    incident_id: int | None = None,
    limit: int = 50,
    _actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    items = search_cases(
        q=q,
        status=status,
        assigned_to_user_id=assigned_to_user_id,
        incident_id=incident_id,
        limit=limit,
    )
    return {"cases": items, "count": len(items)}


@router.post("")
def api_create_case(
    body: CaseCreateIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    try:
        created = create_case(
            title=body.title,
            summary=body.summary,
            incident_id=body.incident_id,
            verification_check_id=body.verification_check_id,
            institution_id=body.institution_id,
            region=body.region,
            priority=body.priority,
            created_by_user_id=actor["id"] if actor else None,
            assigned_to_user_id=body.assigned_to_user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="case.create",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="case",
        resource_id=str(created["id"]),
        ip_address=request.client.host if request.client else None,
    )
    if created.get("assigned_to_user_id"):
        notify_case_assignment(
            case_id=created["id"],
            assignee_user_id=created["assigned_to_user_id"],
            title=created["title"],
        )
    return created


@router.get("/{case_id}")
def api_get_case(
    case_id: int,
    _actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.patch("/{case_id}")
def api_patch_case(
    case_id: int,
    body: CaseUpdateIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    try:
        updated = update_case(
            case_id,
            status=body.status,
            priority=body.priority,
            summary=body.summary,
            title=body.title,
            region=body.region,
            assigned_to_user_id=body.assigned_to_user_id,
            assigned_by_user_id=actor["id"] if actor else None,
            assignment_note=body.assignment_note,
        )
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    write_audit_log(
        action="case.update",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="case",
        resource_id=str(case_id),
        details=body.model_dump(exclude_none=True),
        ip_address=request.client.host if request.client else None,
    )
    if body.assigned_to_user_id:
        notify_case_assignment(case_id=case_id, assignee_user_id=body.assigned_to_user_id, title=updated["title"])
    return updated


@router.post("/{case_id}/assign")
def api_assign_case(
    case_id: int,
    body: CaseAssignIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    try:
        updated = update_case(
            case_id,
            assigned_to_user_id=body.assignee_user_id,
            assigned_by_user_id=actor["id"] if actor else None,
            assignment_note=body.note,
            status=body.status or "investigating",
        )
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    notify_case_assignment(case_id=case_id, assignee_user_id=body.assignee_user_id, title=updated["title"])
    write_audit_log(
        action="case.assign",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="case",
        resource_id=str(case_id),
        details={"assignee_user_id": body.assignee_user_id},
        ip_address=request.client.host if request.client else None,
    )
    return updated


@router.get("/{case_id}/notes")
def api_list_notes(
    case_id: int,
    _actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    if not get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    notes = list_case_notes(case_id)
    return {"notes": notes, "count": len(notes)}


@router.post("/{case_id}/notes")
def api_add_note(
    case_id: int,
    body: CaseNoteIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    try:
        note = add_case_note(
            case_id,
            body=body.body,
            author_user_id=actor["id"] if actor else None,
            author_role=actor["role"] if actor else None,
        )
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    write_audit_log(
        action="case.note",
        actor_user_id=actor["id"] if actor else None,
        actor_role=actor["role"] if actor else None,
        resource_type="case",
        resource_id=str(case_id),
        ip_address=request.client.host if request.client else None,
    )
    return note


@router.get("/{case_id}/assignments")
def api_assignments(
    case_id: int,
    _actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    if not get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    items = list_case_assignments(case_id)
    return {"assignments": items, "count": len(items)}


@router.get("/{case_id}/evidence")
def api_evidence(
    case_id: int,
    _actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    try:
        return evidence_for_case(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{case_id}/workspace")
def api_workspace(
    case_id: int,
    _actor: Annotated[dict | None, Depends(require_permission("incidents:review"))] = None,
):
    try:
        return build_investigation_workspace(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
