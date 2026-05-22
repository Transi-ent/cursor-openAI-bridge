#!/usr/bin/env bash
# 从 config.yaml 读取 server.port（依赖已安装依赖的 venv）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -x ".venv/bin/python" ]]; then
  PY=".venv/bin/python"
elif [[ -x ".venv/Scripts/python.exe" ]]; then
  PY=".venv/Scripts/python.exe"
else
  PY="${PYTHON:-python3}"
fi
exec "$PY" -c "from src.config import load_settings; print(load_settings().port)"
