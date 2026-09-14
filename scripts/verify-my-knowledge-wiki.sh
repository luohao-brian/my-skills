#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" scripts/tests/test_my_knowledge_wiki.py
"$PYTHON_BIN" openclaw-skills/my-knowledge-wiki/scripts/knowledge_query.py --help >/dev/null

printf 'OK: my-knowledge-wiki protocol verification passed\n'

