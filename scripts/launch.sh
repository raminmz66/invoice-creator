#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PIDFILE="$ROOT/.server.pid"
PORTFILE="$ROOT/.server.port"
DEFAULT_PORT=8000
MAX_PORT=$((DEFAULT_PORT + 10))
URL=""

export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

cd "$ROOT"

notify_error() {
  if command -v notify-send >/dev/null 2>&1; then
    notify-send "Invoice Creator" "$1" 2>/dev/null || true
  fi
  echo "Invoice Creator: $1" >&2
}

is_our_server() {
  local port="$1"
  curl -s "http://127.0.0.1:${port}/generate" 2>/dev/null | grep -q "Invoice Creator"
}

open_browser() {
  xdg-open "$URL" >/dev/null 2>&1 &
}

port_is_listening() {
  (echo >/dev/tcp/127.0.0.1/"$1") 2>/dev/null
}

find_running_port() {
  local port
  for port in $(seq "$DEFAULT_PORT" "$MAX_PORT"); do
    if is_our_server "$port"; then
      echo "$port"
      return 0
    fi
  done
  return 1
}

find_free_port() {
  local port
  for port in $(seq "$DEFAULT_PORT" "$MAX_PORT"); do
    if is_our_server "$port"; then
      echo "$port"
      return 0
    fi
    if ! port_is_listening "$port"; then
      echo "$port"
      return 0
    fi
  done
  return 1
}

if [[ -f "$PIDFILE" ]]; then
  pid="$(cat "$PIDFILE")"
  if ! kill -0 "$pid" 2>/dev/null; then
    rm -f "$PIDFILE"
  elif running_port="$(find_running_port)"; then
    URL="http://127.0.0.1:${running_port}"
    echo "$running_port" > "$PORTFILE"
    open_browser
    exit 0
  else
    rm -f "$PIDFILE"
  fi
fi

if running_port="$(find_running_port)"; then
  URL="http://127.0.0.1:${running_port}"
  echo "$running_port" > "$PORTFILE"
  open_browser
  exit 0
fi

# Install uv, the interpreter and the locked dependencies if they are missing.
# Sourced rather than exec'd so the launcher inherits the PATH uv is installed on.
# shellcheck source=bootstrap.sh
source "$ROOT/scripts/bootstrap.sh"

if ! bootstrap; then
  exit 1
fi

UV="$(command -v uv)"

if ! PORT="$(find_free_port)"; then
  notify_error "No free port between ${DEFAULT_PORT} and ${MAX_PORT}."
  exit 1
fi

if is_our_server "$PORT"; then
  URL="http://127.0.0.1:${PORT}"
  echo "$PORT" > "$PORTFILE"
  open_browser
  exit 0
fi

URL="http://127.0.0.1:${PORT}"
echo "$PORT" > "$PORTFILE"

"$UV" run uvicorn app.main:app --host 127.0.0.1 --port "$PORT" &
echo $! > "$PIDFILE"

for _ in $(seq 1 30); do
  if is_our_server "$PORT"; then
    open_browser
    exit 0
  fi
  if ! kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    rm -f "$PIDFILE" "$PORTFILE"
    notify_error "Server exited before becoming ready on ${URL}."
    exit 1
  fi
  sleep 0.5
done

rm -f "$PIDFILE"
notify_error "Failed to start on ${URL}."
exit 1
