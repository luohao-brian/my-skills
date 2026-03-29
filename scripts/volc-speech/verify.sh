#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common.sh
source "$SCRIPT_DIR/../common.sh"

if [[ "${1:-}" == "--live" ]]; then
  LIVE_MODE=1
fi

section "volc-speech"

help_out="$(cargo_out volc-speech-help)"
tts_help_out="$(cargo_out volc-speech-tts-help)"
stt_help_out="$(cargo_out volc-speech-stt-help)"
tts_live_out="$(cargo_out volc-speech-tts-live)"
stt_live_out="$(cargo_out volc-speech-stt-live)"
tts_audio="$TMP_DIR/volc-speech-regression.mp3"

run_capture "CLI help" "$help_out" cargo run -q -p volc-speech --manifest-path "$RUST_DIR/Cargo.toml" -- --help
assert_contains "$help_out" "tts" "main help lists tts"
assert_contains "$help_out" "stt" "main help lists stt"

run_capture "tts help" "$tts_help_out" cargo run -q -p volc-speech --manifest-path "$RUST_DIR/Cargo.toml" -- tts --help
assert_contains "$tts_help_out" "--speaker" "tts help lists --speaker"
assert_contains "$tts_help_out" "--output" "tts help lists --output"

run_capture "stt help" "$stt_help_out" cargo run -q -p volc-speech --manifest-path "$RUST_DIR/Cargo.toml" -- stt --help
assert_contains "$stt_help_out" "--json" "stt help lists --json"

if ! need_live; then
  skip "live checks disabled; run with --live to hit speech APIs"
  exit 0
fi

tts_ready=0
stt_ready=0
if assert_env_any VOLC_TTS_APP_ID VOLC_AUDIO_APP_ID TTS_APP_ID; then
  if assert_env_any VOLC_TTS_ACCESS_KEY VOLC_AUDIO_ACCESS_KEY TTS_ACCESS_KEY; then
    tts_ready=1
  fi
fi
if assert_env_any VOLC_STT_APP_ID VOLC_AUDIO_APP_ID VOLC_APP_ID; then
  if assert_env_any VOLC_STT_ACCESS_KEY VOLC_AUDIO_ACCESS_KEY VOLC_ACCESS_KEY; then
    stt_ready=1
  fi
fi

if [[ "$tts_ready" == "1" ]]; then
  rm -f "$tts_audio"
  run_capture "live tts smoke" "$tts_live_out" cargo run -q -p volc-speech --manifest-path "$RUST_DIR/Cargo.toml" -- tts "回归测试" --output "$tts_audio"
  assert_contains "$tts_live_out" "$tts_audio" "tts output references audio path"
  assert_file_exists "$tts_audio" "tts wrote audio file"
else
  skip "TTS credentials missing; skipping live TTS smoke"
fi

if [[ "$stt_ready" == "1" ]]; then
  stt_input="${VERIFY_VOLC_SPEECH_STT_FILE:-$tts_audio}"
  if [[ -f "$stt_input" ]]; then
    run_capture "live stt smoke" "$stt_live_out" cargo run -q -p volc-speech --manifest-path "$RUST_DIR/Cargo.toml" -- stt "$stt_input"
    assert_contains "$stt_live_out" "text" "stt returns JSON text field"
  else
    skip "STT input file missing; set VERIFY_VOLC_SPEECH_STT_FILE or enable TTS credentials"
  fi
else
  skip "STT credentials missing; skipping live STT smoke"
fi
