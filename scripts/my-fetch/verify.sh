#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common.sh
source "$SCRIPT_DIR/../common.sh"

if [[ "${1:-}" == "--live" ]]; then
  LIVE_MODE=1
fi

section "my-fetch"

test_out="$(cargo_out my-fetch-test)"
help_out="$(cargo_out my-fetch-help)"
html_out="$(cargo_out my-fetch-html)"
json_out="$(cargo_out my-fetch-json)"

run_capture "unit tests" "$test_out" cargo test -p my-fetch --manifest-path "$RUST_DIR/Cargo.toml"
assert_contains "$test_out" "test result: ok." "my-fetch tests pass"

run_capture "CLI help" "$help_out" cargo run -q -p my-fetch --manifest-path "$RUST_DIR/Cargo.toml" -- --help
assert_contains "$help_out" "--selector" "help lists --selector"
assert_contains "$help_out" "--http-proxy" "help lists --http-proxy"
assert_contains "$help_out" "--jina" "help lists --jina"

if ! need_live; then
  skip "live checks disabled; run with --live to hit real URLs"
  exit 0
fi

run_capture "live HTML smoke" "$html_out" cargo run -q -p my-fetch --manifest-path "$RUST_DIR/Cargo.toml" -- "https://httpbin.org/html"
assert_contains "$html_out" "[web_fetch]" "html smoke returns web_fetch header"
assert_contains "$html_out" "status: 200" "html smoke returns 200"

run_capture "live JSON smoke" "$json_out" cargo run -q -p my-fetch --manifest-path "$RUST_DIR/Cargo.toml" -- "https://httpbin.org/json" --format text
assert_contains "$json_out" "\"slideshow\"" "json smoke returns formatted body"
