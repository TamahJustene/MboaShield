"""Background worker tasks: intel, vault retention, AI evaluation."""

from __future__ import annotations

from typing import Any

from ..core.metrics import record_worker_task
from .celery_app import celery_app


@celery_app.task(name="mboashield.intel_ingest", bind=True)
def task_intel_ingest(self, source_id: int) -> dict[str, Any]:
    from ..intel_store import ingest_source

    try:
        result = ingest_source(source_id)
        record_worker_task("intel_ingest", "ok")
        return result
    except Exception as exc:  # noqa: BLE001
        record_worker_task("intel_ingest", "error")
        raise self.retry(exc=exc, countdown=30, max_retries=3) from exc


@celery_app.task(name="mboashield.vault_retention")
def task_vault_retention(dry_run: bool = False) -> dict[str, Any]:
    from ..vault_store import run_retention

    try:
        result = run_retention(dry_run=dry_run)
        record_worker_task("vault_retention", "ok")
        return result
    except Exception:
        record_worker_task("vault_retention", "error")
        raise


@celery_app.task(name="mboashield.ai_evaluation")
def task_ai_evaluation(dataset: str = "en", created_by_user_id: int | None = None) -> dict[str, Any]:
    from ..services.ai.evaluation import run_evaluation

    try:
        result = run_evaluation(dataset=dataset, created_by_user_id=created_by_user_id)
        record_worker_task("ai_evaluation", "ok")
        return result
    except Exception:
        record_worker_task("ai_evaluation", "error")
        raise
