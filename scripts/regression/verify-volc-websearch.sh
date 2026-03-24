#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

if [[ "${1:-}" == "--live" ]]; then
  LIVE_MODE=1
fi

section "volc-websearch"

test_out="$(cargo_out volc-websearch-test)"
help_out="$(cargo_out volc-websearch-help)"
tavily_out="$(cargo_out volc-websearch-tavily)"
brave_out="$(cargo_out volc-websearch-brave)"
bocha_out="$(cargo_out volc-websearch-bocha)"
volc_out="$(cargo_out volc-websearch-volc)"
auto_out="$(cargo_out volc-websearch-auto)"

run_capture "unit tests" "$test_out" cargo test -p volc-websearch --manifest-path "$RUST_DIR/Cargo.toml"
assert_contains "$test_out" "test result: ok." "volc-websearch tests pass"

run_capture "CLI help" "$help_out" cargo run -q -p volc-websearch --manifest-path "$RUST_DIR/Cargo.toml" -- --help
assert_contains "$help_out" "--freshness" "help lists --freshness"
assert_contains "$help_out" "--domain-filter" "help lists --domain-filter"
assert_contains "$help_out" "--result-type" "help lists --result-type"

if ! need_live; then
  skip "live checks disabled; run with --live to hit search providers"
  exit 0
fi

if [[ -n "${TAVILY_API_KEY:-}" ]]; then
  run_capture "live Tavily smoke" "$tavily_out" cargo run -q -p volc-websearch --manifest-path "$RUST_DIR/Cargo.toml" -- --engine tavily --freshness pw --domain-filter openai.com,platform.openai.com --intent source_finding --result-type summary --count 3 "Responses API"
  assert_contains "$tavily_out" "结果数:" "tavily smoke returns results"
else
  skip "TAVILY_API_KEY missing; skipping Tavily smoke"
fi

if [[ -n "${BRAVE_API_KEY:-}" ]]; then
  run_capture "live Brave smoke" "$brave_out" cargo run -q -p volc-websearch --manifest-path "$RUST_DIR/Cargo.toml" -- --engine brave --country US --language en --intent fact --count 3 "interest rates"
  assert_contains "$brave_out" "结果数:" "brave smoke returns results"
else
  skip "BRAVE_API_KEY missing; skipping Brave smoke"
fi

if [[ -n "${BOCHA_API_KEY:-}" ]]; then
  run_capture "live Bocha smoke" "$bocha_out" cargo run -q -p volc-websearch --manifest-path "$RUST_DIR/Cargo.toml" -- --engine bocha --count 3 --intent news "社会新闻"
  assert_contains "$bocha_out" "结果数:" "bocha smoke returns results"
else
  skip "BOCHA_API_KEY missing; skipping Bocha smoke"
fi

if [[ -n "${VE_ACCESS_KEY:-}" && -n "${VE_SECRET_KEY:-}" ]]; then
  run_capture "live Volc smoke" "$volc_out" cargo run -q -p volc-websearch --manifest-path "$RUST_DIR/Cargo.toml" -- --engine volc --domain-filter openai.com,platform.openai.com --intent source_finding --result-type summary --count 3 "Responses API"
  assert_contains "$volc_out" "结果数:" "volc smoke returns results"
else
  skip "VE_ACCESS_KEY/VE_SECRET_KEY missing; skipping Volc smoke"
fi

has_any_search_creds=0
if [[ -n "${TAVILY_API_KEY:-}" || -n "${BRAVE_API_KEY:-}" || -n "${BOCHA_API_KEY:-}" ]]; then
  has_any_search_creds=1
fi
if [[ -n "${VE_ACCESS_KEY:-}" && -n "${VE_SECRET_KEY:-}" ]]; then
  has_any_search_creds=1
fi

if [[ "$has_any_search_creds" == "1" ]]; then
  run_capture "live auto smoke" "$auto_out" cargo run -q -p volc-websearch --manifest-path "$RUST_DIR/Cargo.toml" -- --engine auto --freshness pw --country US --language en --count 3 "AI agent progress"
  assert_contains "$auto_out" "结果数:" "auto smoke returns results"
else
  skip "no search credentials found; skipping auto smoke"
fi
