#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PORT="$("$ROOT/scripts/port.sh" 2>/dev/null || echo 8787)"
LOCAL="http://127.0.0.1:${PORT}"

if ! curl -sf "${LOCAL}/health" >/dev/null 2>&1; then
  echo "Proxy is not running on ${LOCAL}"
  echo "Start it first: ./start.sh"
  exit 1
fi

if ! command -v ngrok >/dev/null 2>&1; then
  echo "ngrok is not installed."
  echo "  macOS:  brew install ngrok/ngrok/ngrok"
  echo "  Linux:  https://ngrok.com/download"
  echo "  auth:   ngrok config add-authtoken <token>"
  exit 1
fi

echo "Tunneling ${LOCAL} via ngrok ..."
echo ""
echo "Find:  Forwarding  https://xxxx.ngrok-free.app -> ${LOCAL}"
echo "Cursor Override OpenAI Base URL = https://xxxx.ngrok-free.app/v1"
echo ""
echo "Press Ctrl+C to stop the tunnel."
echo ""

exec ngrok http "${PORT}"
