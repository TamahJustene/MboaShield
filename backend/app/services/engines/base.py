"""Shared intelligence engine contract.

Every engine returns explainable outputs and never claims certainty.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def clamp(score: int | float) -> int:
    return max(0, min(100, int(round(score))))


def risk_band(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


@dataclass
class EngineResult:
    engine_id: str
    engine_name: str
    confidence: int
    evidence: list[dict[str, Any]] = field(default_factory=list)
    reasoning: str = ""
    risk_level: str = "low"
    risk_score: int = 0
    threat_category: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    status: str = "ok"  # ok | skipped | unsupported | error
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "confidence": clamp(self.confidence),
            "evidence": self.evidence,
            "reasoning": self.reasoning,
            "risk_level": self.risk_level,
            "risk_score": clamp(self.risk_score),
            "threat_category": self.threat_category,
            "recommendations": self.recommendations,
            "status": self.status,
            "details": self.details,
            "certainty": "none",
            "honesty_note": (
                "This engine provides calibrated signals and explainable reasoning. "
                "It does not claim absolute certainty."
            ),
        }


def skipped(engine_id: str, engine_name: str, reason: str) -> EngineResult:
    return EngineResult(
        engine_id=engine_id,
        engine_name=engine_name,
        confidence=0,
        reasoning=reason,
        risk_level="low",
        risk_score=0,
        status="skipped",
        recommendations=["Provide relevant input for this engine to contribute."],
    )


def unsupported(engine_id: str, engine_name: str, capability: str) -> EngineResult:
    return EngineResult(
        engine_id=engine_id,
        engine_name=engine_name,
        confidence=20,
        reasoning=f"{capability} is scaffolded for future deployment and not active yet.",
        risk_level="low",
        risk_score=0,
        status="unsupported",
        recommendations=[f"Keep {engine_id} disabled in production until a validated model is attached."],
        details={"model_ready": False},
    )
