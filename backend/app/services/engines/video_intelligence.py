from __future__ import annotations

from .base import unsupported


def analyze(*, filename: str = "", data: bytes | None = None) -> object:
    return unsupported(
        "video_intelligence",
        "Video Intelligence",
        "Frame-level video deepfake analysis",
    )
