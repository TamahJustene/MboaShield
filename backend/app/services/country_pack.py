"""Country pack and sector catalog (T7)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..core.config import ROOT, get_settings

PACKS_ROOT = ROOT / "deploy" / "country-packs"

SECTOR_CATALOG: list[dict[str, str]] = [
    {
        "id": "election",
        "name": "Election integrity",
        "description": "Impersonation, rumour, and advisory monitoring around electoral periods",
    },
    {
        "id": "health",
        "name": "Health misinformation",
        "description": "Medical rumour and fake authority messaging risk signals",
    },
    {
        "id": "finance",
        "name": "Financial fraud & scams",
        "description": "Mobile-money and institutional impersonation patterns",
    },
]


@lru_cache
def _read_pack_file(pack_id: str) -> dict[str, Any]:
    path = PACKS_ROOT / pack_id / "pack.json"
    if not path.is_file():
        path = PACKS_ROOT / "template" / "pack.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_country_pack(pack_id: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    pid = (pack_id or settings.country_pack or "cm").strip().lower()
    pack = dict(_read_pack_file(pid))
    pack["active"] = True
    pack["resolved_pack_id"] = pack.get("pack_id") or pid
    pack["tenant_id"] = settings.tenant_id
    pack["tenant_display_name"] = settings.tenant_display_name
    pack["path"] = f"deploy/country-packs/{pid}"
    return pack


def list_available_packs() -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    if not PACKS_ROOT.is_dir():
        return items
    for child in sorted(PACKS_ROOT.iterdir()):
        if child.is_dir() and (child / "pack.json").is_file():
            data = json.loads((child / "pack.json").read_text(encoding="utf-8"))
            items.append(
                {
                    "pack_id": data.get("pack_id") or child.name,
                    "name": data.get("name") or child.name,
                    "iso_country": data.get("iso_country") or "",
                }
            )
    return items


def enabled_sectors() -> list[dict[str, Any]]:
    settings = get_settings()
    raw = (settings.sectors_enabled or "").strip()
    if not raw:
        pack = load_country_pack()
        enabled_ids = list(pack.get("default_sectors") or ["election", "health", "finance"])
    else:
        enabled_ids = [item.strip().lower() for item in raw.split(",") if item.strip()]
    catalog = {item["id"]: item for item in SECTOR_CATALOG}
    result: list[dict[str, Any]] = []
    for sid in enabled_ids:
        base = catalog.get(sid, {"id": sid, "name": sid, "description": "Custom sector"})
        result.append({**base, "enabled": True})
    for item in SECTOR_CATALOG:
        if item["id"] not in enabled_ids:
            result.append({**item, "enabled": False})
    return result


def sectors_summary() -> dict[str, Any]:
    items = enabled_sectors()
    return {
        "sectors": items,
        "enabled_ids": [item["id"] for item in items if item.get("enabled")],
        "catalog": SECTOR_CATALOG,
        "config_env": "SECTORS_ENABLED",
    }
