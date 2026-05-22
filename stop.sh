#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PORT="$("$ROOT/scripts/port.sh" 2>/dev/null || echo 8787)"
echo "Stopping Cursor OpenAI Bridge on port ${PORT} ..."

pids=""

if command -v lsof >/dev/null 2>&1; then
  pids="$(lsof -ti :"${PORT}" 2>/dev/null || true)"
elif command -v fuser >/dev/null 2>&1; then
  if fuser "${PORT}/tcp" >/dev/null 2>&1; then
    fuser -k "${PORT}/tcp" >/dev/null 2>&1 || true
    echo "Stopped process(es) on port ${PORT}."
    exit 0
  fi
else
  echo "Neither lsof nor fuser found. Install lsof (macOS/Linux)."
  exit 1
fi

if [[ -z "${pids}" ]]; then
  echo "No process is listening on port ${PORT} (proxy may already be stopped)."
  exit 0
fi

for pid in ${pids}; do
  echo "Stopping PID ${pid} ..."
  kill -9 "${pid}" 2>/dev/null || true
done

echo "Proxy stopped on port ${PORT}."
