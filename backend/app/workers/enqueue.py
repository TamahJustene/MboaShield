"""Enqueue helpers - sync fallback when WORKERS_ENABLED is false."""

from __future__ import annotations

from typing import Any


def workers_active() -> bool:
    from ..core.config import get_settings

    return bool(get_settings().workers_enabled)


def enqueue_intel_ingest(source_id: int) -> dict[str, Any]:
    from ..intel_store import ingest_source

    if not workers_active():
        return {"mode": "sync", "result": ingest_source(source_id)}
    from .tasks import task_intel_ingest

    async_result = task_intel_ingest.delay(source_id)
    return {"mode": "async", "task_id": async_result.id, "source_id": source_id}


def enqueue_vault_retention(*, dry_run: bool = False) -> dict[str, Any]:
    from ..vault_store import run_retention

    if not workers_active():
        return {"mode": "sync", "result": run_retention(dry_run=dry_run)}
    from .tasks import task_vault_retention

    async_result = task_vault_retention.delay(dry_run=dry_run)
    return {"mode": "async", "task_id": async_result.id, "dry_run": dry_run}


def enqueue_ai_evaluation(*, dataset: str = "en", created_by_user_id: int | None = None) -> dict[str, Any]:
    from ..services.ai.evaluation import run_evaluation

    if not workers_active():
        return {
            "mode": "sync",
            "result": run_evaluation(dataset=dataset, created_by_user_id=created_by_user_id),
        }
    from .tasks import task_ai_evaluation

    async_result = task_ai_evaluation.delay(dataset=dataset, created_by_user_id=created_by_user_id)
    return {"mode": "async", "task_id": async_result.id, "dataset": dataset}
