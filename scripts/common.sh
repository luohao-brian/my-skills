#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
RUST_DIR="$ROOT_DIR/rust"
TMP_DIR="${TMPDIR:-/tmp}/my-skills-verification"
mkdir -p "$TMP_DIR"

LIVE_MODE="${LIVE_MODE:-0}"

color() {
  local code="$1"
  shift
  printf '\033[%sm%s\033[0m\n' "$code" "$*"
}

section() {
  color "1;34" ""
  color "1;34" "==> $*"
}

info() {
  color "0;36" "  - $*"
}

pass() {
  color "0;32" "  OK: $*"
}

skip() {
  color "0;33" "  SKIP: $*"
}

fail() {
  color "0;31" "  FAIL: $*" >&2
  exit 1
}

run_cmd() {
  local label="$1"
  shift
  info "$label"
  "$@"
}

run_capture() {
  local label="$1"
  local outfile="$2"
  shift 2
  info "$label"
  "$@" >"$outfile"
}

assert_contains() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if rg -q --fixed-strings -- "$pattern" "$file"; then
    pass "$label"
  else
    printf '\n---- %s ----\n' "$file" >&2
    sed -n '1,200p' "$file" >&2 || true
    fail "$label"
  fi
}

assert_file_exists() {
  local path="$1"
  local label="$2"
  if [[ -f "$path" ]]; then
    pass "$label"
  else
    fail "$label"
  fi
}

assert_env_any() {
  local name
  for name in "$@"; do
    if [[ -n "${!name:-}" ]]; then
      return 0
    fi
  done
  return 1
}

need_live() {
  [[ "$LIVE_MODE" == "1" ]]
}

cargo_out() {
  local name="$1"
  printf '%s/%s.out' "$TMP_DIR" "$name"
}
