"""Advanced AI platform APIs (Phase 12)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request

from ...ai_store import (
    ensure_builtin_models,
    get_calibration_summary,
    latest_evaluation,
    list_models,
    register_model,
    verify_model_checksum,
)
from ...core.config import get_settings
from ...repositories import write_audit_log
from ...schemas import AiModelRegisterIn, AiEvaluationRunIn
from ...services.ai.evaluation import run_evaluation
from ...services.ai.runtime import runtime_status
from ..deps import require_permission

router = APIRouter(prefix="/ai-platform", tags=["pillar-ai"])


def _ensure_ai():
    if not get_settings().advanced_ai_enabled:
        raise HTTPException(status_code=404, detail="Advanced AI platform is disabled")


def _actor_id(actor: dict | None) -> int | None:
    return actor["id"] if actor and actor.get("id") is not None else None


@router.get("/health")
def api_ai_health():
    _ensure_ai()
    ensure_builtin_models()
    return {
        "enabled": True,
        "engine_package_version": "1.2.0",
        "models": len(list_models()),
        "runtimes": runtime_status(),
        "calibration": get_calibration_summary(),
    }


@router.get("/models")
def api_list_models(
    enabled_only: bool = False,
    _actor: Annotated[dict | None, Depends(require_permission("ai:read"))] = None,
):
    _ensure_ai()
    ensure_builtin_models()
    items = list_models(enabled_only=enabled_only)
    return {"models": items, "count": len(items)}


@router.post("/models")
def api_register_model(
    body: AiModelRegisterIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("ai:manage"))] = None,
):
    _ensure_ai()
    try:
        created = register_model(
            model_id=body.model_id,
            name=body.name,
            modality=body.modality,
            runtime=body.runtime,
            version=body.version,
            checksum_sha256=body.checksum_sha256,
            config=body.config,
            enabled=body.enabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="ai.model_register",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="ai_model",
        resource_id=created["model_id"],
        ip_address=request.client.host if request.client else None,
    )
    return created


@router.get("/models/{model_id}/verify-checksum")
def api_verify_checksum(
    model_id: str,
    _actor: Annotated[dict | None, Depends(require_permission("ai:read"))] = None,
):
    _ensure_ai()
    try:
        return verify_model_checksum(model_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/calibration")
def api_calibration(
    _actor: Annotated[dict | None, Depends(require_permission("ai:read"))] = None,
):
    _ensure_ai()
    return get_calibration_summary()


@router.post("/evaluation/run")
def api_run_evaluation(
    body: AiEvaluationRunIn,
    request: Request,
    actor: Annotated[dict | None, Depends(require_permission("ai:manage"))] = None,
):
    _ensure_ai()
    try:
        result = run_evaluation(dataset=body.dataset, created_by_user_id=_actor_id(actor))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="ai.evaluation_run",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="ai_evaluation",
        resource_id=result["run"]["run_id"],
        details={"dataset": body.dataset, "pass_rate": result["metrics"].get("pass_rate")},
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/evaluation/latest")
def api_latest_evaluation(
    dataset: str | None = None,
    _actor: Annotated[dict | None, Depends(require_permission("ai:read"))] = None,
):
    _ensure_ai()
    row = latest_evaluation(dataset=dataset)
    if not row:
        raise HTTPException(status_code=404, detail="No evaluation runs yet")
    return row


@router.get("/monitoring")
def api_monitoring(
    _actor: Annotated[dict | None, Depends(require_permission("ai:read"))] = None,
):
    _ensure_ai()
    latest_en = latest_evaluation(dataset="en")
    latest_fr = latest_evaluation(dataset="fr")
    return {
        "runtimes": runtime_status(),
        "calibration": get_calibration_summary(),
        "latest_evaluations": {
            "en": latest_en,
            "fr": latest_fr,
        },
        "certainty": "none",
    }
