#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
[[ -x "$PYTHON_BIN" ]] || command -v "$PYTHON_BIN" >/dev/null 2>&1 || { printf 'FAIL: %s is required\n' "$PYTHON_BIN" >&2; exit 1; }

export PYTHONDONTWRITEBYTECODE=1
"$PYTHON_BIN" scripts/tests/test_ark_skill_protocols.py
printf 'OK: Ark skill protocol tests\n'
