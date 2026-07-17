"""Celery application factory (Phase 13)."""

from __future__ import annotations

from celery import Celery

from ..core.config import get_settings


def create_celery() -> Celery:
    settings = get_settings()
    app = Celery(
        "mboashield",
        broker=settings.resolved_celery_broker(),
        backend=settings.resolved_celery_backend(),
        include=["backend.app.workers.tasks"],
    )
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        worker_prefetch_multiplier=1,
        beat_schedule={
            "vault-retention-hourly": {
                "task": "mboashield.vault_retention",
                "schedule": 3600.0,
                "kwargs": {"dry_run": False},
            },
        },
    )
    return app


celery_app = create_celery()
