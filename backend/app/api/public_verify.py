"""Public announcement verification (permanent URLs)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from ..announcement_store import (
    build_certificate,
    certificate_markdown,
    verify_announcement,
)
from ..core.config import get_settings

router = APIRouter(tags=["public-verify"])


def _ensure_comms():
    if not get_settings().verified_comms_enabled:
        raise HTTPException(status_code=404, detail="Verified communications are disabled")


@router.get("/verify/a/{announcement_id}")
def public_verify_announcement(
    announcement_id: str,
    v: int | None = Query(default=None, alias="v"),
):
    """Permanent public verification endpoint."""
    _ensure_comms()
    try:
        return verify_announcement(announcement_id, version_number=v)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/verify/a/{announcement_id}/certificate")
def public_certificate(
    announcement_id: str,
    v: int | None = Query(default=None, alias="v"),
    format: str = "json",
):
    _ensure_comms()
    try:
        cert = build_certificate(announcement_id, version_number=v)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if format == "markdown":
        return PlainTextResponse(certificate_markdown(cert), media_type="text/markdown")
    return cert
