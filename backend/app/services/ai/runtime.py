"""Runtime adapters for Phase 12 advanced AI (heuristic fallback always available)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class RuntimeAdapter(Protocol):
    runtime_id: str

    def analyze_text(self, *, text: str, lang: str = "en") -> dict[str, Any] | None:
        ...

    def available(self) -> bool:
        ...


@dataclass
class HeuristicRuntime:
    runtime_id: str = "heuristic"

    def available(self) -> bool:
        return True

    def analyze_text(self, *, text: str, lang: str = "en") -> dict[str, Any] | None:
        from ..engines import text_intelligence

        result = text_intelligence.analyze(text=text, lang=lang)
        return result.as_dict()


@dataclass
class OnnxRuntimeAdapter:
    runtime_id: str = "onnx"

    def available(self) -> bool:
        try:
            import onnxruntime  # noqa: F401
        except ImportError:
            return False
        return False  # No bundled ONNX models in demo profile

    def analyze_text(self, *, text: str, lang: str = "en") -> dict[str, Any] | None:
        return None


def select_runtime(runtime: str) -> RuntimeAdapter:
    if runtime == "onnx":
        adapter = OnnxRuntimeAdapter()
        if adapter.available():
            return adapter
    return HeuristicRuntime()


def runtime_status() -> dict[str, Any]:
    onnx = OnnxRuntimeAdapter()
    return {
        "heuristic": {"available": True, "default": True},
        "onnx": {"available": onnx.available(), "default": False},
        "transformers": {"available": False, "note": "Enable in government profile with model artifacts"},
        "whisper": {"available": False, "note": "Audio path uses feature-model adapter"},
    }
