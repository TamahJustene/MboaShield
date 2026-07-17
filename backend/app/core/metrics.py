"""Prometheus metrics for MboaShield (Phase 13)."""

from __future__ import annotations

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .config import get_settings

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
except ImportError:  # pragma: no cover - optional until requirements installed
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
    Counter = Gauge = Histogram = None  # type: ignore
    generate_latest = None  # type: ignore

REQUEST_COUNT = None
REQUEST_LATENCY = None
WORKER_TASKS = None
APP_INFO = None


def _init_metrics() -> None:
    global REQUEST_COUNT, REQUEST_LATENCY, WORKER_TASKS, APP_INFO
    if Counter is None or REQUEST_COUNT is not None:
        return
    REQUEST_COUNT = Counter(
        "mboashield_http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status"],
    )
    REQUEST_LATENCY = Histogram(
        "mboashield_http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["method", "path"],
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    )
    WORKER_TASKS = Counter(
        "mboashield_worker_tasks_total",
        "Background worker task outcomes",
        ["task", "status"],
    )
    APP_INFO = Gauge(
        "mboashield_app_info",
        "Application info (1 = present)",
        ["version", "profile"],
    )


def refresh_app_info() -> None:
    _init_metrics()
    if APP_INFO is None:
        return
    settings = get_settings()
    APP_INFO.labels(version=settings.version, profile=settings.deployment_profile).set(1)


def record_worker_task(task: str, status: str) -> None:
    _init_metrics()
    if WORKER_TASKS is None:
        return
    WORKER_TASKS.labels(task=task, status=status).inc()


def metrics_payload() -> tuple[bytes, str]:
    _init_metrics()
    refresh_app_info()
    if generate_latest is None:
        body = b"# prometheus_client not installed\n"
        return body, "text/plain; charset=utf-8"
    return generate_latest(), CONTENT_TYPE_LATEST


def normalize_path(path: str) -> str:
    if path.startswith("/static"):
        return "/static"
    parts = path.split("/")
    out: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.isdigit() or (len(part) > 20 and "-" in part):
            out.append(":id")
        else:
            out.append(part)
    return "/" + "/".join(out) if out else "/"


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not get_settings().metrics_enabled or REQUEST_COUNT is None:
            _init_metrics()
        if not get_settings().metrics_enabled or REQUEST_COUNT is None:
            return await call_next(request)
        if request.url.path == "/metrics":
            return await call_next(request)
        started = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - started
        path = normalize_path(request.url.path)
        REQUEST_COUNT.labels(method=request.method, path=path, status=str(response.status_code)).inc()
        if REQUEST_LATENCY is not None:
            REQUEST_LATENCY.labels(method=request.method, path=path).observe(elapsed)
        return response
