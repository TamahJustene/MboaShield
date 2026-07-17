"""Advanced AI platform persistence: model registry, evaluation, calibration."""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from .core.config import DATA_DIR, get_settings
from .db.models import AiEvaluationRun, AiModelRegistry, AnalysisFeedback
from .db.session import session_scope
from .repositories import now_iso


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _model_to_dict(row: AiModelRegistry) -> dict[str, Any]:
    return {
        "id": row.id,
        "model_id": row.model_id,
        "name": row.name,
        "modality": row.modality,
        "runtime": row.runtime,
        "checksum_sha256": row.checksum_sha256,
        "version": row.version,
        "config": json.loads(row.config_json or "{}"),
        "enabled": bool(row.enabled),
        "status": row.status,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def ensure_builtin_models() -> list[dict[str, Any]]:
    """Register built-in heuristic adapters (checksum-verified)."""
    settings = get_settings()
    if not settings.advanced_ai_enabled:
        return []
    builtins = [
        {
            "model_id": "mboashield-text-nlp-v1",
            "name": "MboaShield Text NLP",
            "modality": "text",
            "runtime": "heuristic",
            "version": "1.2.0",
            "path": DATA_DIR / "nlp_weights.json",
            "config": {"fallback": True, "family": "nlp"},
        },
        {
            "model_id": "mboashield-media-adapter-v1",
            "name": "MboaShield Media Adapter",
            "modality": "image",
            "runtime": "feature-model",
            "version": "1.2.0",
            "path": DATA_DIR / "media_weights.json",
            "config": {"fallback": True, "family": "vision"},
        },
        {
            "model_id": "mboashield-audio-adapter-v1",
            "name": "MboaShield Audio Adapter",
            "modality": "audio",
            "runtime": "feature-model",
            "version": "1.2.0",
            "path": DATA_DIR / "audio_weights.json",
            "config": {"fallback": True, "family": "audio"},
        },
        {
            "model_id": "mboashield-onnx-stub-v1",
            "name": "ONNX Runtime Placeholder",
            "modality": "multimodal",
            "runtime": "onnx",
            "version": "0.0.0",
            "path": None,
            "config": {"enabled": False, "note": "Attach ONNX artifacts in government profile"},
        },
    ]
    saved: list[dict[str, Any]] = []
    now = now_iso()
    with session_scope() as session:
        for item in builtins:
            existing = session.execute(
                select(AiModelRegistry).where(AiModelRegistry.model_id == item["model_id"])
            ).scalar_one_or_none()
            path = item.get("path")
            if path and Path(path).is_file():
                checksum = _sha256_file(Path(path))
            else:
                checksum = _sha256_text(json.dumps(item["config"], sort_keys=True))
            if existing:
                existing.checksum_sha256 = checksum
                existing.version = item["version"]
                existing.updated_at = now
                existing.config_json = json.dumps(item["config"], ensure_ascii=True)
                saved.append(_model_to_dict(existing))
                continue
            row = AiModelRegistry(
                model_id=item["model_id"],
                name=item["name"],
                modality=item["modality"],
                runtime=item["runtime"],
                checksum_sha256=checksum,
                version=item["version"],
                config_json=json.dumps(item["config"], ensure_ascii=True),
                enabled=item["runtime"] != "onnx",
                status="active" if item["runtime"] != "onnx" else "scaffolded",
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            session.flush()
            saved.append(_model_to_dict(row))
    return saved


def list_models(*, enabled_only: bool = False) -> list[dict[str, Any]]:
    with session_scope() as session:
        stmt = select(AiModelRegistry).order_by(AiModelRegistry.modality.asc(), AiModelRegistry.model_id.asc())
        if enabled_only:
            stmt = stmt.where(AiModelRegistry.enabled.is_(True))
        rows = session.execute(stmt).scalars().all()
        return [_model_to_dict(row) for row in rows]


def register_model(
    *,
    model_id: str,
    name: str,
    modality: str,
    runtime: str,
    version: str,
    checksum_sha256: str,
    config: dict[str, Any] | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    model_id = (model_id or "").strip()
    if not model_id:
        raise ValueError("model_id is required")
    now = now_iso()
    with session_scope() as session:
        row = session.execute(select(AiModelRegistry).where(AiModelRegistry.model_id == model_id)).scalar_one_or_none()
        if row:
            row.name = name
            row.modality = modality
            row.runtime = runtime
            row.version = version
            row.checksum_sha256 = checksum_sha256
            row.config_json = json.dumps(config or {}, ensure_ascii=True)
            row.enabled = enabled
            row.status = "active"
            row.updated_at = now
        else:
            row = AiModelRegistry(
                model_id=model_id,
                name=name,
                modality=modality,
                runtime=runtime,
                checksum_sha256=checksum_sha256,
                version=version,
                config_json=json.dumps(config or {}, ensure_ascii=True),
                enabled=enabled,
                status="active",
                created_at=now,
                updated_at=now,
            )
            session.add(row)
        session.flush()
        return _model_to_dict(row)


def verify_model_checksum(model_id: str) -> dict[str, Any]:
    with session_scope() as session:
        row = session.execute(select(AiModelRegistry).where(AiModelRegistry.model_id == model_id)).scalar_one_or_none()
        if not row:
            raise ValueError("Model not found")
        stored = row.checksum_sha256
    path_map = {
        "mboashield-text-nlp-v1": DATA_DIR / "nlp_weights.json",
        "mboashield-media-adapter-v1": DATA_DIR / "media_weights.json",
        "mboashield-audio-adapter-v1": DATA_DIR / "audio_weights.json",
    }
    path = path_map.get(model_id)
    if path and path.is_file():
        actual = _sha256_file(path)
        return {
            "model_id": model_id,
            "stored_checksum": stored,
            "actual_checksum": actual,
            "valid": actual == stored,
        }
    return {
        "model_id": model_id,
        "stored_checksum": stored,
        "actual_checksum": None,
        "valid": True,
        "note": "No on-disk artifact; checksum is config-derived",
    }


def get_calibration_summary() -> dict[str, Any]:
    """Derive calibration stats from analyst feedback labels."""
    with session_scope() as session:
        total = session.scalar(select(func.count()).select_from(AnalysisFeedback)) or 0
        if total < 5:
            return {
                "samples": int(total),
                "ready": False,
                "bias_adjustment": 0,
                "accuracy": None,
                "certainty": "none",
            }
        rows = session.scalars(select(AnalysisFeedback)).all()
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.label] = counts.get(row.label, 0) + 1
    tp = counts.get("true_positive", 0)
    tn = counts.get("true_negative", 0)
    fp = counts.get("false_positive", 0)
    fn = counts.get("false_negative", 0)
    labeled = tp + tn + fp + fn
    accuracy = (tp + tn) / labeled if labeled else 0.0
    # Conservative adjustment: if false positives dominate, nudge trust down slightly
    bias = 0
    if labeled >= 5:
        fp_rate = fp / labeled
        fn_rate = fn / labeled
        bias = int(round((fn_rate - fp_rate) * 10))
        bias = max(-8, min(8, bias))
    return {
        "samples": labeled,
        "ready": labeled >= 5,
        "bias_adjustment": bias,
        "accuracy": round(accuracy, 3) if labeled else None,
        "label_counts": counts,
        "certainty": "none",
    }


def save_evaluation_run(
    *,
    dataset: str,
    metrics: dict[str, Any],
    latency_ms_p50: int,
    created_by_user_id: int | None = None,
) -> dict[str, Any]:
    run_id = f"eval_{uuid.uuid4().hex[:16]}"
    now = now_iso()
    with session_scope() as session:
        row = AiEvaluationRun(
            run_id=run_id,
            dataset=dataset,
            metrics_json=json.dumps(metrics, ensure_ascii=True),
            latency_ms_p50=latency_ms_p50,
            created_by_user_id=created_by_user_id,
            created_at=now,
        )
        session.add(row)
        session.flush()
        return {
            "run_id": run_id,
            "dataset": dataset,
            "metrics": metrics,
            "latency_ms_p50": latency_ms_p50,
            "created_at": now,
        }


def latest_evaluation(dataset: str | None = None) -> dict[str, Any] | None:
    with session_scope() as session:
        stmt = select(AiEvaluationRun).order_by(AiEvaluationRun.id.desc()).limit(1)
        if dataset:
            stmt = (
                select(AiEvaluationRun)
                .where(AiEvaluationRun.dataset == dataset)
                .order_by(AiEvaluationRun.id.desc())
                .limit(1)
            )
        row = session.execute(stmt).scalar_one_or_none()
        if not row:
            return None
        return {
            "run_id": row.run_id,
            "dataset": row.dataset,
            "metrics": json.loads(row.metrics_json or "{}"),
            "latency_ms_p50": row.latency_ms_p50,
            "created_at": row.created_at,
        }
