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
  skills=(volc-gen volc-speech volc-websearch ai-news)
fi

run_skill() {
  local skill="$1"
  case "$skill" in
    volc-gen)
      LIVE_MODE="$LIVE_MODE" bash "$SCRIPT_DIR/volc-gen/verify.sh"
      ;;
    volc-speech)
      LIVE_MODE="$LIVE_MODE" bash "$SCRIPT_DIR/volc-speech/verify.sh"
      ;;
    volc-websearch)
      LIVE_MODE="$LIVE_MODE" bash "$SCRIPT_DIR/volc-websearch/verify.sh"
      ;;
    ai-news)
      LIVE_MODE="$LIVE_MODE" bash "$SCRIPT_DIR/ai-news/verify.sh"
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

printf '\nAll requested verification checks completed.\n'
