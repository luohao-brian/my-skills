#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CLI_DIR="$SCRIPT_DIR/cli"
TARGET_DIR="/usr/local/bin"

if [[ ! -d "$CLI_DIR" ]]; then
  echo "Error: cli directory not found: $CLI_DIR" >&2
  exit 1
fi

installed=0
for cmd in "$CLI_DIR"/*; do
  if [[ -f "$cmd" && -x "$cmd" ]]; then
    name="$(basename "$cmd")"
    ln -sf "$cmd" "$TARGET_DIR/$name"
    echo "Installed: $TARGET_DIR/$name -> $cmd"
    installed=$((installed + 1))
  fi
done

if [[ "$installed" -eq 0 ]]; then
  echo "No executable commands found in $CLI_DIR"
else
  echo "Done. Installed $installed command(s)."
fi
