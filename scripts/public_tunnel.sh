#!/usr/bin/env bash
# Quick public URL for form submission (no account needed)
# Requires: cloudflared  OR  ngrok
set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${PORT:-8000}"

if ! curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
  echo "Starting MboaShield on port ${PORT}..."
  PYTHONPATH=. python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port "$PORT" &
  sleep 2
fi

if command -v cloudflared >/dev/null 2>&1; then
  echo "Public URL (Cloudflare Tunnel):"
  exec cloudflared tunnel --url "http://127.0.0.1:${PORT}"
elif command -v ngrok >/dev/null 2>&1; then
  echo "Public URL (ngrok):"
  exec ngrok http "$PORT"
else
  echo "Install cloudflared or ngrok for instant public URL."
  echo "Or deploy free on Render: see docs/DEPLOY.md"
  exit 1
fi
