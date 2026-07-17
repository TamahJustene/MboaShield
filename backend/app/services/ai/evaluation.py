"""Golden-set evaluation harness for intelligence engines."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ...core.config import DATA_DIR, get_settings
from ..engines import analyze_intelligence
from ...ai_store import save_evaluation_run


def _load_dataset(name: str) -> list[dict[str, Any]]:
    path = DATA_DIR / f"ai_golden_{name}.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("cases") or [])


def run_evaluation(
    *,
    dataset: str = "en",
    created_by_user_id: int | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    if not settings.advanced_ai_enabled:
        raise ValueError("ADVANCED_AI_ENABLED is false")
    cases = _load_dataset(dataset)
    if not cases:
        raise ValueError(f"Golden dataset ai_golden_{dataset}.json is missing or empty")

    latencies: list[float] = []
    passed = 0
    results: list[dict[str, Any]] = []
    for case in cases:
        started = time.perf_counter()
        analysis = analyze_intelligence(
            text=case.get("text") or "",
            name=case.get("name") or "",
            handle=case.get("handle") or "",
            url=case.get("url") or "",
            lang=case.get("lang") or dataset,
            include_scaffolds=False,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        latencies.append(elapsed_ms)
        risk = analysis["trust_score"]["fused_risk_score"]
        min_risk = int(case.get("expect_min_risk") or 0)
        max_risk = int(case.get("expect_max_risk") or 100)
        ok = min_risk <= risk <= max_risk
        if ok:
            passed += 1
        results.append(
            {
                "id": case.get("id"),
                "risk": risk,
                "expect_min_risk": min_risk,
                "expect_max_risk": max_risk,
                "passed": ok,
                "latency_ms": round(elapsed_ms, 2),
            }
        )

    latencies.sort()
    p50 = int(latencies[len(latencies) // 2]) if latencies else 0
    metrics = {
        "dataset": dataset,
        "cases": len(cases),
        "passed": passed,
        "pass_rate": round(passed / len(cases), 3) if cases else 0.0,
        "latency_budget_ms": settings.ai_eval_latency_budget_ms,
        "latency_p50_ms": p50,
        "latency_within_budget": p50 <= settings.ai_eval_latency_budget_ms,
        "results": results,
        "certainty": "none",
    }
    saved = save_evaluation_run(
        dataset=dataset,
        metrics=metrics,
        latency_ms_p50=p50,
        created_by_user_id=created_by_user_id,
    )
    return {"run": saved, "metrics": metrics}
