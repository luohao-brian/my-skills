#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

LIVE_MODE=0
if [[ "${1:-}" == "--live" ]]; then
  LIVE_MODE=1
  shift
fi

skills=("$@")
if [[ "${#skills[@]}" == 0 ]]; then
  skills=(volc-gen volc-speech volc-websearch)
fi

run_skill() {
  local skill="$1"
  case "$skill" in
    volc-gen)
      LIVE_MODE="$LIVE_MODE" bash "$SCRIPT_DIR/verify-volc-gen.sh"
      ;;
    volc-speech)
      LIVE_MODE="$LIVE_MODE" bash "$SCRIPT_DIR/verify-volc-speech.sh"
      ;;
    volc-websearch)
      LIVE_MODE="$LIVE_MODE" bash "$SCRIPT_DIR/verify-volc-websearch.sh"
      ;;
    *)
      printf 'Unknown skill: %s\n' "$skill" >&2
      exit 1
      ;;
  esac
}

for skill in "${skills[@]}"; do
  run_skill "$skill"
done

printf '\nAll requested regression checks completed.\n'
