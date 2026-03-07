#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CLI_DIR="$SCRIPT_DIR/cli"
TARGET_DIR="/usr/local/bin"

if [[ ! -d "$CLI_DIR" ]]; then
  echo "Error: cli directory not found: $CLI_DIR" >&2
  exit 1
fi

removed=0
for cmd in "$CLI_DIR"/*; do
  if [[ -f "$cmd" ]]; then
    name="$(basename "$cmd")"
    target="$TARGET_DIR/$name"
    if [[ -L "$target" || -f "$target" ]]; then
      rm -f "$target"
      echo "Removed: $target"
      removed=$((removed + 1))
    fi
  fi
done

if [[ "$removed" -eq 0 ]]; then
  echo "No command links/files removed from $TARGET_DIR"
else
  echo "Done. Removed $removed command(s)."
fi
