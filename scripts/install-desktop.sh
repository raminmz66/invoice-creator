#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$DESKTOP_DIR/invoice-creator.desktop"

mkdir -p "$DESKTOP_DIR"
sed "s|@INSTALL_ROOT@|$ROOT|g" "$ROOT/invoice-creator.desktop.in" > "$DESKTOP_FILE"
chmod +x "$ROOT/scripts/launch.sh"
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
echo "Installed: $DESKTOP_FILE"
