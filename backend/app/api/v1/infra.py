"""Enterprise infrastructure status and job enqueue APIs (Phase 13)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ...core.config import get_settings
from ...repositories import write_audit_log
from ...workers.enqueue import (
    enqueue_ai_evaluation,
    enqueue_intel_ingest,
    enqueue_vault_retention,
    workers_active,
)
from ..deps import require_permission

router = APIRouter(prefix="/infra", tags=["infra"])


def _actor_id(actor: dict | None) -> int | None:
    return actor["id"] if actor and actor.get("id") is not None else None


@router.get("/status")
def api_infra_status():
    settings = get_settings()
    redis_ok = False
    if settings.redis_url.strip():
        try:
            import redis

            client = redis.from_url(settings.redis_url, socket_connect_timeout=1)
            redis_ok = bool(client.ping())
        except Exception:  # noqa: BLE001
            redis_ok = False
    return {
        "version": settings.version,
        "metrics_enabled": settings.metrics_enabled,
        "workers_enabled": settings.workers_enabled,
        "workers_active": workers_active(),
        "redis": {"configured": bool(settings.redis_url.strip()), "reachable": redis_ok},
        "celery": {
            "broker": settings.resolved_celery_broker().split("@")[-1] if settings.workers_enabled else None,
            "backend_configured": bool(settings.resolved_celery_backend()),
        },
        "database": "postgresql" if settings.resolved_database_url().startswith("postgresql") else "sqlite",
        "deployment_profile": settings.deployment_profile,
    }


@router.post("/jobs/intel-ingest/{source_id}")
def api_enqueue_intel(
    source_id: int,
    actor: Annotated[dict | None, Depends(require_permission("intel:manage"))],
):
    try:
        result = enqueue_intel_ingest(source_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="infra.intel_ingest",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="intel_source",
        resource_id=str(source_id),
        details={"mode": result.get("mode")},
    )
    return result


@router.post("/jobs/vault-retention")
def api_enqueue_retention(
    actor: Annotated[dict | None, Depends(require_permission("evidence:manage"))],
    dry_run: bool = True,
):
    result = enqueue_vault_retention(dry_run=dry_run)
    write_audit_log(
        action="infra.vault_retention",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="evidence_retention",
        resource_id="run",
        details={"mode": result.get("mode"), "dry_run": dry_run},
    )
    return result


@router.post("/jobs/ai-evaluation")
def api_enqueue_ai_eval(
    actor: Annotated[dict | None, Depends(require_permission("ai:manage"))],
    dataset: str = "en",
):
    if dataset not in {"en", "fr"}:
        raise HTTPException(status_code=400, detail="dataset must be en or fr")
    try:
        result = enqueue_ai_evaluation(dataset=dataset, created_by_user_id=_actor_id(actor))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit_log(
        action="infra.ai_evaluation",
        actor_user_id=_actor_id(actor),
        actor_role=(actor or {}).get("role"),
        resource_type="ai_evaluation",
        resource_id=dataset,
        details={"mode": result.get("mode"), "dataset": dataset},
    )
    return result
