from __future__ import annotations

import re
from urllib.parse import urlparse

from .base import EngineResult, clamp, risk_band, skipped

URL_RE = re.compile(r"https?://[^\s]+", re.I)
SUSPICIOUS_TLDS = {".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".icu"}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly"}


def analyze(*, text: str = "", url: str = "") -> EngineResult:
    urls = []
    if url.strip():
        urls.append(url.strip())
    urls.extend(URL_RE.findall(text or ""))
    if not urls:
        return skipped("network_intelligence", "Network Intelligence", "No URL or network indicator provided.")

    evidence = []
    score = 20
    threats: list[str] = []
    for item in urls[:5]:
        parsed = urlparse(item if "://" in item else f"http://{item}")
        host = (parsed.hostname or "").lower()
        evidence.append({"label": f"Observed URL host: {host or item}", "weight": 10, "kind": "network_signal"})
        if any(host.endswith(tld) for tld in SUSPICIOUS_TLDS):
            score += 25
            evidence.append({"label": f"Suspicious TLD on {host}", "weight": 16, "kind": "network_risk"})
            threats.append("scam")
        if host in SHORTENERS:
            score += 18
            evidence.append({"label": f"Link shortener used: {host}", "weight": 14, "kind": "network_risk"})
            threats.append("social_engineering")
        if host.count(".") >= 3:
            score += 10
            evidence.append({"label": f"Deep subdomain pattern: {host}", "weight": 11, "kind": "network_risk"})

    score = clamp(score)
    return EngineResult(
        engine_id="network_intelligence",
        engine_name="Network Intelligence",
        confidence=clamp(42 + len(evidence) * 5),
        evidence=evidence,
        reasoning="URLs and hosts were screened for shortener use, unusual TLDs, and deep subdomain patterns.",
        risk_level=risk_band(score),
        risk_score=score,
        threat_category=list(dict.fromkeys(threats)),
        recommendations=[
            "Open official domains typed manually rather than forwarded short links.",
            "Inspect the final destination before authenticating.",
        ],
        details={"urls": urls[:5]},
    )
