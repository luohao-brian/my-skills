#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

NODE_BIN="${NODE_BIN:-node}"
[[ -x "$NODE_BIN" ]] || command -v "$NODE_BIN" >/dev/null 2>&1 || { printf 'FAIL: %s is required\n' "$NODE_BIN" >&2; exit 1; }

VISUAL=false
if [[ "${1:-}" == "--visual" ]]; then
  VISUAL=true
  shift
fi
[[ "$#" -eq 0 ]] || { printf 'Usage: bash scripts/verify-guizang-ppt-skill.sh [--visual]\n' >&2; exit 2; }

SKILL_DIR="openclaw-skills/guizang-ppt-skill"
"$NODE_BIN" "$SKILL_DIR/scripts/build-swiss-golden.mjs" --check
"$NODE_BIN" "$SKILL_DIR/scripts/check-presenter-runtime-sync.mjs"
"$NODE_BIN" "$SKILL_DIR/scripts/verify-swiss-contract.mjs"
"$NODE_BIN" "$SKILL_DIR/scripts/validate-swiss-deck.mjs" "$SKILL_DIR/assets/swiss-golden.html"
"$NODE_BIN" "$SKILL_DIR/scripts/validate-presenter-mode.mjs" "$SKILL_DIR/assets/swiss-golden.html"

if [[ "$VISUAL" == true ]]; then
  OUTPUT_DIR="${TMPDIR:-/tmp}/guizang-ppt-visual-check"
  "$NODE_BIN" "$SKILL_DIR/scripts/visual-check-swiss.mjs" "$SKILL_DIR/assets/swiss-golden.html" --output "$OUTPUT_DIR"
fi

printf 'OK: guizang-ppt-skill verification passed\n'
