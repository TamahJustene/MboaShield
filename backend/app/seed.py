from __future__ import annotations

import json

from sqlalchemy import func, select

from .config import DATA_DIR
from .db.models import Institution
from .db.session import session_scope
from .repositories import now_iso


def seed_institutions_if_needed() -> int:
    with session_scope() as session:
        count = session.scalar(select(func.count()).select_from(Institution)) or 0
        if count:
            return 0

        raw = json.loads((DATA_DIR / "institutions.json").read_text(encoding="utf-8"))
        stamp = now_iso()
        for item in raw:
            session.add(
                Institution(
                    id=item["id"],
                    name=item["name"],
                    short_name=item["short_name"],
                    website_url=item.get("url", ""),
                    verified=1 if item.get("verified", True) else 0,
                    handles_json=json.dumps(item.get("handles", []), ensure_ascii=True),
                    created_at=stamp,
                )
            )
        return len(raw)
