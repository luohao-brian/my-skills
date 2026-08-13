#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_BIN="$PYTHON_BIN"
elif [[ -x "$HOME/Documents/hermes-workspace/.venv/bin/python" ]]; then
  PYTHON_BIN="$HOME/Documents/hermes-workspace/.venv/bin/python"
else
  PYTHON_BIN=python3
fi
[[ -x "$PYTHON_BIN" ]] || command -v "$PYTHON_BIN" >/dev/null 2>&1 || { printf 'FAIL: %s is required\n' "$PYTHON_BIN" >&2; exit 1; }

export PYTHONDONTWRITEBYTECODE=1
"$PYTHON_BIN" scripts/verify-ppt-master-runtime.py
"$PYTHON_BIN" -m unittest discover -s openclaw-skills/ppt-master/scripts/tests -p 'test_*.py'
"$PYTHON_BIN" scripts/tests/test_ppt_master_sync.py
printf 'OK: ppt-master verification passed\n'
