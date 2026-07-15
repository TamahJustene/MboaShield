#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install -r backend/requirements.txt
fi
export PYTHONPATH=.
exec .venv/bin/uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
