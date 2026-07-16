"""Lightweight local NLP model path for rumour/scam text scoring.

Uses lexicon-feature vectors + calibrated linear weights (stdlib only).
Designed so a transformer/ONNX model can replace `score_text_nlp()` later
without changing API contracts.
"""

from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from typing import Any

from ..config import DATA_DIR


@lru_cache(maxsize=1)
def _load_weights() -> dict[str, Any]:
    path = DATA_DIR / "nlp_weights.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", (text or "").lower())


def _lexicon_density(text: str, phrases: list[str]) -> float:
    lowered = (text or "").lower()
    if not lowered.strip():
        return 0.0
    hits = sum(1 for phrase in phrases if phrase in lowered)
    return min(1.0, hits / max(2.0, len(phrases) * 0.25))


def extract_features(text: str) -> dict[str, float]:
    weights = _load_weights()
    lexicons = weights.get("lexicons", {})
    raw = text or ""
    tokens = _tokenize(raw)
    token_count = max(len(tokens), 1)

    features = {
        "urgency": _lexicon_density(raw, lexicons.get("urgency", [])),
        "money": _lexicon_density(raw, lexicons.get("money", [])),
        "authority": _lexicon_density(raw, lexicons.get("authority", [])),
        "rumour": _lexicon_density(raw, lexicons.get("rumour", [])),
        "prize": _lexicon_density(raw, lexicons.get("prize", [])),
        "threat": _lexicon_density(raw, lexicons.get("threat", [])),
        "no_link": 1.0 if len(raw) > 40 and not re.search(r"https?://|www\.", raw.lower()) else 0.0,
        "shouting": 1.0
        if re.search(r"[A-Z]{6,}", raw) and sum(1 for c in raw if c.isupper()) > len(raw) * 0.35
        else 0.0,
        "length_norm": min(1.0, len(tokens) / 40.0),
        "fr_markers": min(
            1.0,
            sum(1 for t in tokens if t in {"le", "la", "les", "de", "des", "une", "pour"}) / 8.0,
        ),
        "en_markers": min(
            1.0,
            sum(1 for t in tokens if t in {"the", "and", "for", "with", "this", "that"}) / 8.0,
        ),
    }
    features["token_count"] = float(token_count)
    return features


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def score_text_nlp(text: str) -> dict[str, Any]:
    """Return NLP model score in 0..100 with explainable top features."""
    cfg = _load_weights()
    features = extract_features(text)
    weight_map: dict[str, float] = cfg.get("weights", {})
    bias = float(cfg.get("bias", 0.0))

    linear = bias
    contributions: list[tuple[str, float, float]] = []
    for key, weight in weight_map.items():
        value = float(features.get(key, 0.0))
        contrib = weight * value
        linear += contrib
        if value > 0:
            contributions.append((key, value, contrib))

    probability = _sigmoid(linear * 3.2)
    score = int(round(probability * 100))
    contributions.sort(key=lambda item: item[2], reverse=True)

    reasons = []
    for key, value, contrib in contributions[:5]:
        reasons.append(
            f"NLP feature '{key}' activated ({value:.2f}, weight contribution {contrib:.2f})"
        )

    if not reasons:
        reasons.append("NLP model found weak lexical risk features")

    return {
        "engine": cfg.get("name", "mboashield-text-nlp-v1"),
        "engine_version": cfg.get("version", "1.0.0"),
        "risk_score": max(0, min(100, score)),
        "probability": round(probability, 4),
        "features": {k: round(v, 4) for k, v in features.items() if k != "token_count"},
        "top_features": [
            {"name": key, "value": round(value, 4), "contribution": round(contrib, 4)}
            for key, value, contrib in contributions[:5]
        ],
        "reasons": reasons,
    }
