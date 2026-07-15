"""Mboa Ambassadors learning + certificate stub."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from ..config import DATA_DIR


def list_lessons() -> list[dict]:
    return json.loads((DATA_DIR / "lessons.json").read_text(encoding="utf-8"))


def complete_lesson(lesson_id: str, learner_name: str) -> dict:
    lessons = {item["id"]: item for item in list_lessons()}
    lesson = lessons.get(lesson_id)
    if not lesson:
        return {"ok": False, "error": "Unknown lesson_id"}

    name = (learner_name or "").strip() or "Citizen"
    cert_id = str(uuid.uuid4())[:8].upper()
    issued = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return {
        "ok": True,
        "certificate": {
            "id": f"MBOA-{cert_id}",
            "learner_name": name,
            "lesson_id": lesson_id,
            "lesson_title_en": lesson["title_en"],
            "lesson_title_fr": lesson["title_fr"],
            "issued_on": issued,
            "issuer": "MboaShield  Digital Patriotism Track",
            "founder": "Justene Nkwagoh Tamah",
        },
    }
