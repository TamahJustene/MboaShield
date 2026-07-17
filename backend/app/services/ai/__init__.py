"""AI platform package."""

from .evaluation import run_evaluation
from .runtime import runtime_status, select_runtime

__all__ = ["run_evaluation", "runtime_status", "select_runtime"]
