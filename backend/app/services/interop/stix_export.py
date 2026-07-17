"""STIX 2.1 read-only export from intel items (T4 pilot)."""

from __future__ import annotations

import uuid
from typing import Any

from ...intel_store import list_intel_items
from ...repositories import now_iso


def build_stix_bundle(*, limit: int = 50, query: str | None = None) -> dict[str, Any]:
    items = list_intel_items(q=query, limit=limit)
    stamp = now_iso()
    objects: list[dict[str, Any]] = []
    for item in items:
        key = f"mboashield-intel-{item.get('id')}"
        indicator_id = f"indicator--{uuid.uuid5(uuid.NAMESPACE_URL, key)}"
        title = (item.get("title") or item.get("summary") or "MboaShield intel item")[:200]
        raw = item.get("url") or item.get("external_id") or title
        pattern_value = str(raw).replace("\\", "\\\\").replace("'", "\\'")
        objects.append(
            {
                "type": "indicator",
                "spec_version": "2.1",
                "id": indicator_id,
                "created": item.get("fetched_at") or stamp,
                "modified": item.get("fetched_at") or stamp,
                "name": title,
                "description": item.get("summary") or title,
                "pattern": f"[url:value = '{pattern_value}']",
                "pattern_type": "stix",
                "valid_from": item.get("fetched_at") or stamp,
                "labels": ["mboashield", "cameroon", item.get("source_class") or "intel"],
                "confidence": 50,
                "x_mboashield_intel_id": item.get("id"),
                "x_mboashield_source_id": item.get("source_id"),
            }
        )

    return {
        "type": "bundle",
        "id": f"bundle--{uuid.uuid4()}",
        "spec_version": "2.1",
        "objects": objects,
        "x_mboashield": {
            "export": "stix-intel-pilot",
            "count": len(objects),
            "generated_at": stamp,
            "note": "Read-only STIX pilot; not a full TAXII 2.1 server.",
        },
    }
