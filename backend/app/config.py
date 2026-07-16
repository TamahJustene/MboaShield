"""Compatibility shim.

Legacy imports (`from backend.app.config import ROOT, VERSION, DATA_DIR, DB_PATH`)
continue to work while settings live in `core.config`.
"""

from __future__ import annotations

from .core.config import DATA_DIR, DB_PATH, ROOT, VERSION, get_settings

__all__ = ["ROOT", "DATA_DIR", "DB_PATH", "VERSION", "get_settings"]
