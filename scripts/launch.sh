#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PIDFILE="$ROOT/.server.pid"
PORT=8000
URL="http://127.0.0.1:$PORT"

cd "$ROOT"

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  xdg-open "$URL" >/dev/null 2>&1 &
  exit 0
fi

if curl -sf "$URL" >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 &
  exit 0
fi

uv run uvicorn app.main:app --host 127.0.0.1 --port "$PORT" &
echo $! > "$PIDFILE"

for i in $(seq 1 30); do
  if curl -sf "$URL" >/dev/null 2>&1; then
    xdg-open "$URL" >/dev/null 2>&1 &
    exit 0
  fi
  sleep 0.5
done

echo "Invoice Creator failed to start on $URL" >&2
exit 1
