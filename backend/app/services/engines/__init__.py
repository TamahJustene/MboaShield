"""Orchestrate modular intelligence engines for multimodal cases."""

from __future__ import annotations

from typing import Any

from . import (
    audio_intelligence,
    behavior_intelligence,
    document_intelligence,
    identity_intelligence,
    image_intelligence,
    metadata_intelligence,
    network_intelligence,
    source_intelligence,
    text_intelligence,
    video_intelligence,
)
from .base import EngineResult
from .trust_fusion import fuse

ENGINE_CATALOG = [
    {
        "id": "text_intelligence",
        "name": "Text Intelligence",
        "status": "active",
        "inputs": ["text"],
    },
    {
        "id": "image_intelligence",
        "name": "Image Intelligence",
        "status": "active",
        "inputs": ["image_bytes", "filename"],
    },
    {
        "id": "audio_intelligence",
        "name": "Audio Intelligence",
        "status": "active",
        "inputs": ["audio_bytes", "filename"],
    },
    {
        "id": "video_intelligence",
        "name": "Video Intelligence",
        "status": "scaffolded",
        "inputs": ["video_bytes"],
    },
    {
        "id": "identity_intelligence",
        "name": "Identity Intelligence",
        "status": "active",
        "inputs": ["name", "handle"],
    },
    {
        "id": "document_intelligence",
        "name": "Document Intelligence",
        "status": "scaffolded",
        "inputs": ["document_bytes"],
    },
    {
        "id": "network_intelligence",
        "name": "Network Intelligence",
        "status": "active",
        "inputs": ["text", "url"],
    },
    {
        "id": "source_intelligence",
        "name": "Source Intelligence",
        "status": "active",
        "inputs": ["text"],
    },
    {
        "id": "behavior_intelligence",
        "name": "Behavior Intelligence",
        "status": "active",
        "inputs": ["text"],
    },
    {
        "id": "metadata_intelligence",
        "name": "Metadata Intelligence",
        "status": "active",
        "inputs": ["filename", "mime_type", "size_bytes"],
    },
]


def list_engines() -> list[dict[str, Any]]:
    return ENGINE_CATALOG


def run_engines(
    *,
    text: str = "",
    name: str = "",
    handle: str = "",
    url: str = "",
    filename: str = "",
    mime_type: str = "",
    size_bytes: int | None = None,
    image_bytes: bytes | None = None,
    audio_bytes: bytes | None = None,
    lang: str = "en",
    include_scaffolds: bool = True,
) -> list[EngineResult]:
    results: list[EngineResult] = [
        text_intelligence.analyze(text=text, lang=lang),
        source_intelligence.analyze(text=text, lang=lang),
        behavior_intelligence.analyze(text=text, lang=lang),
        identity_intelligence.analyze(name=name, handle=handle, lang=lang),
        network_intelligence.analyze(text=text, url=url),
        metadata_intelligence.analyze(filename=filename, mime_type=mime_type, size_bytes=size_bytes),
        image_intelligence.analyze(data=image_bytes, filename=filename, lang=lang),
        audio_intelligence.analyze(data=audio_bytes, filename=filename, lang=lang),
    ]
    if include_scaffolds:
        results.append(video_intelligence.analyze(filename=filename))
        results.append(document_intelligence.analyze(text=text, filename=filename))
    return results


def analyze_intelligence(
    *,
    text: str = "",
    name: str = "",
    handle: str = "",
    url: str = "",
    filename: str = "",
    mime_type: str = "",
    size_bytes: int | None = None,
    image_bytes: bytes | None = None,
    audio_bytes: bytes | None = None,
    lang: str = "en",
    include_scaffolds: bool = True,
) -> dict[str, Any]:
    engines = run_engines(
        text=text,
        name=name,
        handle=handle,
        url=url,
        filename=filename,
        mime_type=mime_type,
        size_bytes=size_bytes,
        image_bytes=image_bytes,
        audio_bytes=audio_bytes,
        lang=lang,
        include_scaffolds=include_scaffolds,
    )
    trust = fuse(engines, lang=lang)
    return {
        "engines": [item.as_dict() for item in engines],
        "trust_score": trust,
        "summary": {
            "active_engines": len([item for item in engines if item.status == "ok"]),
            "skipped_engines": len([item for item in engines if item.status == "skipped"]),
            "scaffolded_engines": len([item for item in engines if item.status == "unsupported"]),
            "top_threats": trust.get("threat_categories", []),
            "explainable_trust_score": trust.get("trust_score"),
        },
    }


def engine_for_modality(modality: str) -> str:
    mapping = {
        "text": "text_intelligence",
        "impersonation": "identity_intelligence",
        "media": "image_intelligence",
        "audio": "audio_intelligence",
        "case": "trust_fusion",
    }
    return mapping.get(modality, "text_intelligence")
