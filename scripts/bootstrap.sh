#!/usr/bin/env bash
# Resolve and install everything the app needs to run: uv, a suitable Python
# interpreter and the locked dependencies. Idempotent and offline once current,
# so it is safe to run on every launch.
#
# Sourced by scripts/launch.sh; also runnable directly:  ./scripts/bootstrap.sh
set -uo pipefail

ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
BOOTSTRAP_LOG="${BOOTSTRAP_LOG:-$ROOT/.server.log}"
UV_INSTALLER_URL="${UV_INSTALLER_URL:-https://astral.sh/uv/install.sh}"
UV_INSTALL_BIN="$HOME/.local/bin"
# Shared libraries WeasyPrint 69 dlopens (see weasyprint/text/ffi.py). Only apt
# can supply these, so we report them rather than installing them.
WEASYPRINT_APT_PACKAGES="libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libfontconfig1 libglib2.0-0"

bootstrap_notify() {
  if command -v notify-send >/dev/null 2>&1; then
    notify-send "Invoice Creator" "$1" 2>/dev/null || true
  fi
}

bootstrap_fail() {
  bootstrap_notify "$1"
  echo "Invoice Creator: $1" >&2
}

# True when this launch has real work to do, i.e. a slow first run worth
# announcing on a launcher that has no terminal.
needs_setup() {
  ! command -v uv >/dev/null 2>&1 || [[ ! -d "$ROOT/.venv" ]]
}

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    return 0
  fi
  { curl -LsSf "$UV_INSTALLER_URL" | sh; } >>"$BOOTSTRAP_LOG" 2>&1 || return 1
  export PATH="$UV_INSTALL_BIN:$PATH"
  command -v uv >/dev/null 2>&1
}

# Resolves and installs the locked dependencies, fetching a managed Python that
# satisfies requires-python if the system one is too old. --inexact keeps
# packages that are not in the lock, so launching does not strip the dev extras.
ensure_deps() {
  (cd "$ROOT" && uv sync --inexact) >>"$BOOTSTRAP_LOG" 2>&1
}

ensure_system_libs() {
  (cd "$ROOT" && uv run python -c "import weasyprint") >>"$BOOTSTRAP_LOG" 2>&1
}

bootstrap() {
  if needs_setup; then
    bootstrap_notify "Setting up dependencies, this may take a minute..."
  fi

  if ! ensure_uv; then
    bootstrap_fail "Could not install uv automatically. Install it by hand: curl -LsSf ${UV_INSTALLER_URL} | sh"
    return 1
  fi

  if ! ensure_deps; then
    bootstrap_fail "Failed to install dependencies. See ${BOOTSTRAP_LOG} for details."
    return 1
  fi

  if ! ensure_system_libs; then
    bootstrap_fail "WeasyPrint cannot load its system libraries. Run: sudo apt install ${WEASYPRINT_APT_PACKAGES}"
    return 1
  fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  bootstrap
fi
