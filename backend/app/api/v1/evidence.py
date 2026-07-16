"""Digital Evidence Vault APIs."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response

from ...core.config import get_settings
from ...repositories import write_audit_log
from ...schemas import EvidenceRegisterIn, EvidenceRetentionIn, EvidenceTransferIn
from ...vault_store import (
    export_evidence,
    get_evidence,
    list_custody,
    list_evidence,
    read_evidence_bytes,
    register_evidence,
    register_evidence_from_base64,
    run_retention,
    transfer_custody,
    verify_custody_chain,
    verify_export,
)
from ..deps import require_permission

router = APIRouter(prefix="/evidence", tags=["evidence"])


def _ensure_vault():
    if not get_settings().vault_enabled:
        raise HTTPException(status_code=404, detail="Evidence vault is disabled")


def _actor_id(actor: dict | None) -> int | None:
    return actor["id"] if actor else None


@router.get("/health")
def api_vault_health():
    _ensure_vault()
    settings = get_settings()
    return {
        "enabled": True,
        "storage": settings.vault_storage,
        "max_bytes": settings.vault_max_bytes,
        "retention_days": settings.vault_retention_days,
    }


@router.post("/retention/run")
def api_retention(
    body: EvidenceRetentionIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("evidence:manage"))] = None,
):
    _ensure_vault()
    result = run_retention(dry_run=body.dry_run)
    write_audit_log(
        action="evidence.retention",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="evidence_retention",
        resource_id="run",
        details={"dry_run": body.dry_run, "count": result["count"]}
    )
    return result


@router.get("/exports/{export_id}/verify")
def api_verify_export(
    export_id: str,
    _actor: Annotated[dict | None, Depends(require_permission("evidence:read"))] = None,
):
    _ensure_vault()
    try:
        return verify_export(export_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("")
@router.post("/")
async def api_register_evidence(
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("evidence:write"))] = None,
    title: str | None = Form(None),
    filename: str | None = Form(None),
    description: str | None = Form(None),
    case_id: int | None = Form(None),
    incident_id: int | None = Form(None),
    verification_check_id: int | None = Form(None),
    retention_days: int | None = Form(None),
    file: UploadFile | None = File(None),
):
    """Register evidence via multipart upload or JSON body."""
    _ensure_vault()
    content_type = request.headers.get("content-type", "")
    try:
        if "application/json" in content_type:
            payload = EvidenceRegisterIn.model_validate(await request.json())
            created = register_evidence_from_base64(
                title=payload.title,
                filename=payload.filename,
                content_base64=payload.content_base64,
                content_type=payload.content_type,
                description=payload.description,
                case_id=payload.case_id,
                incident_id=payload.incident_id,
                verification_check_id=payload.verification_check_id,
                created_by_user_id=_actor_id(actor),
                retention_days=payload.retention_days,
            )
        else:
            if not file or not title or not filename:
                raise HTTPException(
                    status_code=400,
                    detail="Multipart registration requires title, filename, and file",
                )
            data = await file.read()
            created = register_evidence(
                title=title,
                filename=filename,
                content=data,
                content_type=file.content_type or "application/octet-stream",
                description=description,
                case_id=case_id,
                incident_id=incident_id,
                verification_check_id=verification_check_id,
                created_by_user_id=_actor_id(actor),
                retention_days=retention_days,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    write_audit_log(
        action="evidence.register",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="evidence",
        resource_id=created["evidence_id"],
        details={"sha256": created["sha256"], "size_bytes": created["size_bytes"]}
    )
    return created


@router.get("")
@router.get("/")
def api_list_evidence(
    case_id: int | None = None,
    incident_id: int | None = None,
    q: str | None = None,
    status: str | None = None,
    limit: int = 50,
    _actor: Annotated[dict | None, Depends(require_permission("evidence:read"))] = None,
):
    _ensure_vault()
    items = list_evidence(case_id=case_id, incident_id=incident_id, q=q, status=status, limit=limit)
    return {"items": items, "count": len(items)}


@router.get("/{evidence_id}")
def api_get_evidence(
    evidence_id: str,
    _actor: Annotated[dict | None, Depends(require_permission("evidence:read"))] = None,
):
    _ensure_vault()
    item = get_evidence(evidence_id)
    if not item:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return item


@router.get("/{evidence_id}/download")
def api_download_evidence(
    evidence_id: str,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("evidence:read"))] = None,
):
    _ensure_vault()
    try:
        item, data = read_evidence_bytes(evidence_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    write_audit_log(
        action="evidence.download",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="evidence",
        resource_id=evidence_id,
        details={"size_bytes": item["size_bytes"]}
    )
    return Response(
        content=data,
        media_type=item["content_type"],
        headers={"Content-Disposition": f'attachment; filename="{item["filename"]}"'},
    )


@router.get("/{evidence_id}/custody")
def api_custody(
    evidence_id: str,
    _actor: Annotated[dict | None, Depends(require_permission("evidence:read"))] = None,
):
    _ensure_vault()
    if not get_evidence(evidence_id):
        raise HTTPException(status_code=404, detail="Evidence not found")
    events = list_custody(evidence_id)
    chain = verify_custody_chain(evidence_id)
    return {"evidence_id": evidence_id, "events": events, "chain": chain}


@router.post("/{evidence_id}/transfer")
def api_transfer(
    evidence_id: str,
    body: EvidenceTransferIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("evidence:write"))] = None,
):
    _ensure_vault()
    try:
        updated = transfer_custody(
            evidence_id,
            to_user_id=body.to_user_id,
            from_user_id=_actor_id(actor),
            note=body.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="evidence.transfer",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="evidence",
        resource_id=evidence_id,
        details={"to_user_id": body.to_user_id}
    )
    return updated


@router.post("/{evidence_id}/export")
def api_export(
    evidence_id: str,
    request: Request,
    include_content: bool = True,
    actor: Annotated[dict | None, Depends(require_permission("evidence:write"))] = None,
):
    _ensure_vault()
    try:
        exported = export_evidence(
            evidence_id,
            created_by_user_id=_actor_id(actor),
            include_content=include_content,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="evidence.export",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="evidence_export",
        resource_id=exported["export_id"],
        details={"evidence_id": evidence_id, "package_sha256": exported["package_sha256"]}
    )
    return exported
