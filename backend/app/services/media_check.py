"""Lightweight media risk heuristics (plug-in point for real deepfake models)."""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageStat


@dataclass
class MediaCheckResult:
    risk_score: int
    risk_band: str
    reasons: list[str]
    meta: dict
    advice: str

    def as_dict(self) -> dict:
        return {
            "risk_score": self.risk_score,
            "risk_band": self.risk_band,
            "reasons": self.reasons,
            "meta": self.meta,
            "advice": self.advice,
            "engine": "heuristic-v0",
        }


def _band(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def check_image_bytes(data: bytes, filename: str = "", lang: str = "en") -> MediaCheckResult:
    reasons: list[str] = []
    score = 15
    meta: dict = {"filename": filename, "bytes": len(data)}

    try:
        img = Image.open(io.BytesIO(data))
        img = img.convert("RGB")
        w, h = img.size
        meta.update({"width": w, "height": h, "format": img.format})

        # Extremely small images / stickers forwarded as "proof"
        if w * h < 80_000:
            score += 15
            reasons.append("Very small resolution - common for re-compressed viral fakes")

        # Odd aspect often from generative crops
        ratio = w / max(h, 1)
        if ratio < 0.45 or ratio > 2.3:
            score += 10
            reasons.append("Unusual aspect ratio")

        # EXIF absence can be a weak signal for generative images
        exif = img.getexif()
        if not exif or len(exif) == 0:
            score += 20
            reasons.append("No camera EXIF metadata (weak synthetic-media signal)")
        else:
            meta["exif_tags"] = len(exif)
            reasons.append("Camera EXIF present (weaker synthetic signal)")

        # Flat colour variance proxy (oversmoothed AI faces)
        stat = ImageStat.Stat(img)
        mean_var = sum(stat.var) / max(len(stat.var), 1)
        meta["mean_variance"] = round(mean_var, 2)
        if mean_var < 1200:
            score += 28
            reasons.append("Unusually smooth colour variance (possible over-processed / synthetic)")
        elif mean_var > 9000:
            score += 8
            reasons.append("Very noisy / heavily recompressed image")

    except Exception as exc:  # noqa: BLE001 - return safe demo error
        return MediaCheckResult(
            risk_score=50,
            risk_band="medium",
            reasons=[f"Could not fully decode image: {exc}"],
            meta=meta,
            advice="Try another PNG/JPG. For the pitch, use prepared demo samples.",
        )

    score = max(0, min(100, score))
    if not reasons:
        reasons.append("No strong heuristic flags; still verify context")

    if lang.startswith("fr"):
        advice = {
            "high": "Signaux synth?tiques ?lev?s. Ne traitez pas cette image comme une preuve.",
            "medium": "Signaux mixtes. Demandez la source originale (photo brute).",
            "low": "Peu de signaux heuristiques. V?rifiez quand m?me le contexte.",
        }[_band(score)]
    else:
        advice = {
            "high": "Strong synthetic signals. Do not treat this image as proof.",
            "medium": "Mixed signals. Ask for the original source (raw photo).",
            "low": "Few heuristic flags. Still verify context before trusting it.",
        }[_band(score)]

    return MediaCheckResult(
        risk_score=score,
        risk_band=_band(score),
        reasons=reasons[:8],
        meta=meta,
        advice=advice,
    )
