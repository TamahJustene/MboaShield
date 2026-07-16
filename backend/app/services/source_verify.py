"""Lightweight claim verification against local official-source corpus."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from ..config import DATA_DIR

SCAM_TOPICS = [
    "couvre-feu", "curfew", "fermeture banque", "banks closed",
    "gagnez", "you won", "lottery", "momo gratuit", "free money",
    "ministre annonce", "minister announces", "compte bloque", "account blocked",
]


@dataclass
class SourceVerification:
    status: str
    matched_sources: list[dict]
    scam_signals: list[str]
    summary: str

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "matched_sources": self.matched_sources,
            "scam_signals": self.scam_signals,
            "summary": self.summary,
        }


def _load_sources() -> list[dict]:
    return json.loads((DATA_DIR / "sources.json").read_text(encoding="utf-8"))


def verify_claim(text: str, lang: str = "en") -> SourceVerification:
    lowered = (text or "").lower().strip()
    if not lowered:
        return SourceVerification(
            status="unverified",
            matched_sources=[],
            scam_signals=[],
            summary="No text to verify.",
        )

    sources = _load_sources()
    matched: list[dict] = []
    for src in sources:
        title = src.get("title", "").lower()
        for topic in src.get("topics", []):
            if topic in lowered or topic in title:
                matched.append(src)
                break

    scam_signals = [t for t in SCAM_TOPICS if t in lowered]
    has_urgent_money = bool(re.search(r"urgent|momo|argent|money|transfer", lowered))

    if scam_signals and has_urgent_money:
        status = "likely_scam"
        summary = (
            "Aucune source officielle ne confirme ce message; signaux d'arnaque detectes."
            if lang.startswith("fr")
            else "No official source confirms this message; scam signals detected."
        )
    elif matched:
        status = "unverified"
        summary = (
            "Sujet lie a des sources officielles - verifiez directement sur le site avant de partager."
            if lang.startswith("fr")
            else "Topic relates to official sources - verify on the site before sharing."
        )
    else:
        status = "unverified"
        summary = (
            "Non verifie dans le corpus officiel camerounais."
            if lang.startswith("fr")
            else "Not verified in the Cameroon official corpus."
        )

    seen = set()
    unique = []
    for m in matched:
        if m["id"] not in seen:
            seen.add(m["id"])
            unique.append(m)

    return SourceVerification(
        status=status,
        matched_sources=unique[:4],
        scam_signals=scam_signals[:6],
        summary=summary,
    )
