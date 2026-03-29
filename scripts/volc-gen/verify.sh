#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common.sh
source "$SCRIPT_DIR/../common.sh"

if [[ "${1:-}" == "--live" ]]; then
  LIVE_MODE=1
fi

section "volc-gen"

help_out="$(cargo_out volc-gen-help)"
t2i_help_out="$(cargo_out volc-gen-t2i-help)"
query_help_out="$(cargo_out volc-gen-query-help)"
query_live_out="$(cargo_out volc-gen-query-live)"

run_capture "CLI help" "$help_out" cargo run -q -p volc-gen --manifest-path "$RUST_DIR/Cargo.toml" -- --help
assert_contains "$help_out" "t2i" "main help lists t2i"
assert_contains "$help_out" "i2i" "main help lists i2i"
assert_contains "$help_out" "i2v" "main help lists i2v"
assert_contains "$help_out" "query" "main help lists query"

run_capture "t2i help" "$t2i_help_out" cargo run -q -p volc-gen --manifest-path "$RUST_DIR/Cargo.toml" -- t2i --help
assert_contains "$t2i_help_out" "--size" "t2i help lists --size"

run_capture "query help" "$query_help_out" cargo run -q -p volc-gen --manifest-path "$RUST_DIR/Cargo.toml" -- query --help
assert_contains "$query_help_out" "Query task(s)" "query help renders"

if ! need_live; then
  skip "live checks disabled; run with --live to hit Ark API"
  exit 0
fi

if [[ -z "${ARK_API_KEY:-}" ]]; then
  skip "ARK_API_KEY missing; skipping live volc-gen checks"
  exit 0
fi

run_capture "live query smoke" "$query_live_out" cargo run -q -p volc-gen --manifest-path "$RUST_DIR/Cargo.toml" -- query
assert_contains "$query_live_out" "{" "live query returns JSON output"
pass "volc-gen live smoke completed"
