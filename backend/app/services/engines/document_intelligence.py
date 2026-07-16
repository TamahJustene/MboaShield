from __future__ import annotations

from .base import unsupported


def analyze(*, text: str = "", filename: str = "", data: bytes | None = None) -> object:
    return unsupported(
        "document_intelligence",
        "Document Intelligence",
        "Official document authenticity and forgery screening",
    )
