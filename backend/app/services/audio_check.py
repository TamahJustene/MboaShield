"""Voice-note / audio risk heuristics (ML-pluggable, stdlib-first)."""

from __future__ import annotations

import io
import struct
import wave
from dataclasses import dataclass


@dataclass
class AudioCheckResult:
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


def _read_wav(data: bytes) -> tuple[int, int, int, list[int]] | None:
    try:
        with wave.open(io.BytesIO(data), "rb") as wf:
            channels = wf.getnchannels()
            rate = wf.getframerate()
            n_frames = wf.getnframes()
            sampwidth = wf.getsampwidth()
            raw = wf.readframes(min(n_frames, rate * 30))
            if sampwidth == 2:
                count = len(raw) // 2
                samples = struct.unpack(f"<{count}h", raw[: count * 2])
            elif sampwidth == 1:
                samples = [b - 128 for b in raw]
            else:
                return None
            return rate, channels, n_frames, list(samples)
    except Exception:
        return None


def check_audio_bytes(data: bytes, filename: str = "", lang: str = "en") -> AudioCheckResult:
    reasons: list[str] = []
    score = 15
    meta: dict = {"filename": filename, "bytes": len(data)}

    lowered = (filename or "").lower()
    clone_hints = ["voice", "audio", "note", "ministre", "minister", "urgent", "officiel", "clone"]
    if any(h in lowered for h in clone_hints):
        score += 12
        reasons.append("Filename suggests voice-note / institutional impersonation context")

    if len(data) < 8_000:
        score += 10
        reasons.append("Very small audio file (common for forwarded voice-note scams)")

    parsed = _read_wav(data)
    if parsed:
        rate, channels, n_frames, samples = parsed
        duration = n_frames / max(rate, 1)
        meta.update({
            "sample_rate": rate,
            "channels": channels,
            "duration_sec": round(duration, 2),
            "format": "wav",
        })

        if duration < 3:
            score += 15
            reasons.append("Very short clip (< 3s) - typical of viral voice scams")
        elif duration > 120:
            score += 5
            reasons.append("Long audio - harder to verify manually")

        if samples:
            peak = max(abs(s) for s in samples) or 1
            amps = [abs(s) / peak for s in samples[:: max(1, len(samples) // 500)]]
            if amps:
                mean_amp = sum(amps) / len(amps)
                variance = sum((a - mean_amp) ** 2 for a in amps) / len(amps)
                meta["amplitude_variance"] = round(variance, 6)
                if variance < 0.002:
                    score += 22
                    reasons.append("Unusually flat dynamics (possible synthetic / cloned voice)")
                elif variance < 0.008:
                    score += 12
                    reasons.append("Low dynamic variation (weak clone signal)")

        if rate > 48_000:
            score += 8
            reasons.append("High sample rate uncommon for WhatsApp voice notes")
    else:
        meta["format"] = "unknown_or_compressed"
        score += 8
        reasons.append("Compressed/unknown format - verify source manually")

    score = max(0, min(100, score))
    if not reasons:
        reasons.append("No strong voice-clone markers; still verify with official channels")

    if lang.startswith("fr"):
        advice = {
            "high": "Risque eleve de voix clonee. Ne transferez pas d'argent. Verifiez via le site officiel.",
            "medium": "Signaux mixtes. Demandez confirmation ecrite sur un canal officiel.",
            "low": "Peu de signaux audio suspects. Restez vigilant avant toute action.",
        }[_band(score)]
    else:
        advice = {
            "high": "High voice-clone risk. Do not send money. Verify via official website.",
            "medium": "Mixed signals. Demand written confirmation on an official channel.",
            "low": "Few suspicious audio signals. Stay cautious before acting.",
        }[_band(score)]

    return AudioCheckResult(
        risk_score=score,
        risk_band=_band(score),
        reasons=reasons[:8],
        meta=meta,
        advice=advice,
    )
