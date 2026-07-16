from __future__ import annotations

import json

from .config import DATA_DIR
from .db import get_conn, now_iso


def seed_institutions_if_needed() -> int:
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM institutions").fetchone()["c"]
        if count:
            return 0

        raw = json.loads((DATA_DIR / "institutions.json").read_text(encoding="utf-8"))
        for item in raw:
            conn.execute(
                """
                INSERT INTO institutions (
                    id,
                    name,
                    short_name,
                    website_url,
                    verified,
                    handles_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["id"],
                    item["name"],
                    item["short_name"],
                    item.get("url", ""),
                    1 if item.get("verified", True) else 0,
                    json.dumps(item.get("handles", []), ensure_ascii=True),
                    now_iso(),
                ),
            )
        return len(raw)
