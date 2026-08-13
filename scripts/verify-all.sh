#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

GUIZANG_ARGS=()
if [[ "${1:-}" == "--visual" ]]; then
  GUIZANG_ARGS+=(--visual)
  shift
fi
[[ "$#" -eq 0 ]] || { printf 'Usage: bash scripts/verify-all.sh [--visual]\n' >&2; exit 2; }

bash scripts/verify-repo.sh
bash scripts/verify-ark-skills.sh
bash scripts/verify-ppt-master.sh
if [[ "${#GUIZANG_ARGS[@]}" -gt 0 ]]; then
  bash scripts/verify-guizang-ppt-skill.sh "${GUIZANG_ARGS[@]}"
else
  bash scripts/verify-guizang-ppt-skill.sh
fi

printf 'OK: full repository verification passed\n'
