#!/usr/bin/env bash
# Production server (bind all interfaces - for Render/Docker/VPS)
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=.
PORT="${PORT:-8000}"
exec python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port "$PORT"
