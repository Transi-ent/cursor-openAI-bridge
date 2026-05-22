#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — set UPSTREAM_API_KEY before using Cursor."
fi

if [[ ! -d .venv ]]; then
  echo "Creating virtual environment..."
  "$PYTHON" -m venv .venv
fi

if [[ -x ".venv/bin/pip" ]]; then
  PIP=".venv/bin/pip"
  PY=".venv/bin/python"
else
  PIP=".venv/Scripts/pip.exe"
  PY=".venv/Scripts/python.exe"
fi

echo "Installing dependencies..."
"$PIP" install -q -r requirements.txt

PORT="$("$ROOT/scripts/port.sh" 2>/dev/null || echo 8787)"
if [[ -n "${PROXY_CONFIG:-}" ]]; then
  echo "Using config: $PROXY_CONFIG"
fi
echo "Starting Cursor OpenAI Bridge on http://127.0.0.1:${PORT} ..."
exec "$PY" -m uvicorn src.main:app --host 127.0.0.1 --port "$PORT"
