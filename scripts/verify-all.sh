#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

pass() {
  printf 'OK: %s\n' "$*"
}

assert_no_path() {
  local path="$1"
  [[ ! -e "$path" ]] || fail "$path should not exist"
}

assert_file() {
  local path="$1"
  [[ -f "$path" ]] || fail "$path missing"
}

assert_contains() {
  local path="$1"
  local text="$2"
  rg -q --fixed-strings -- "$text" "$path" || fail "$path missing: $text"
}

assert_metadata_single_line() {
  local path="$1"
  if rg -q '^metadata: \{.*\}$' "$path"; then
    return
  fi
  if rg -q '^metadata:' "$path"; then
    fail "$path metadata must be single-line JSON"
  fi
}

assert_no_path rust
assert_no_path cli
assert_no_path dist
assert_no_path build-skill-bundle.sh
assert_no_path my-fetch
assert_no_path volc-gen
assert_no_path volc-speech
assert_no_path volc-websearch

skills=(
  info-track/ai-news
  info-track/ai-labs-tracker
  info-track/reddit-oss-models
  openclaw-skills/tts
  openclaw-skills/stt
  openclaw-skills/image-gen
  openclaw-skills/video-gen
  openclaw-skills/volc-search
)

for skill in "${skills[@]}"; do
  assert_file "$skill/SKILL.md"
  assert_contains "$skill/SKILL.md" "description:"
  assert_metadata_single_line "$skill/SKILL.md"
done

assert_file hermes-plugins/hermes-ark-plugin/plugin.yaml
assert_file hermes-plugins/hermes-ark-plugin/cli.py
assert_file hermes-plugins/hermes-ark-plugin/providers/text_to_speech.py
assert_file hermes-plugins/hermes-ark-plugin/providers/transcribe_audio.py
assert_file hermes-plugins/hermes-ark-plugin/providers/image_generate.py
assert_file hermes-plugins/hermes-ark-plugin/providers/video_generate.py

assert_file pyproject.toml
assert_file uv.lock
assert_contains pyproject.toml "requests>=2.32,<3"
assert_contains uv.lock 'name = "requests"'

assert_contains openclaw-skills/tts/SKILL.md "references/ark-tts.md"
assert_contains openclaw-skills/stt/SKILL.md "references/ark-stt.md"
assert_contains openclaw-skills/image-gen/SKILL.md "references/ark-image-gen.md"
assert_contains openclaw-skills/video-gen/SKILL.md "references/ark-video-gen.md"
assert_contains openclaw-skills/volc-search/SKILL.md "references/docs-index.md"
assert_contains openclaw-skills/volc-search/SKILL.md "融合信息搜索"

assert_file info-track/ai-news/references/sources.json
assert_file info-track/ai-news/references/source-contract.md
assert_file info-track/ai-news/references/output-schema.md
assert_file info-track/ai-news/references/example-candidates.json
assert_file info-track/ai-news/templates/brief.md.tpl
assert_file info-track/ai-news/templates/item.md.tpl
assert_file info-track/ai-news/templates/summarize-prompt.md.tpl
assert_file info-track/ai-news/scripts/ai_news.py
assert_file info-track/ai-news/scripts/adapters/__init__.py
assert_contains info-track/ai-news/SKILL.md "scripts/ai_news.py run"
assert_contains info-track/ai-news/SKILL.md "references/sources.json"
assert_contains info-track/ai-news/SKILL.md "source_coverage"

python_bin=""
if command -v python3 >/dev/null 2>&1; then
  python_bin=python3
elif command -v python >/dev/null 2>&1; then
  python_bin=python
else
  fail "python3 or python is required for syntax checks"
fi

PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/my-skills-pycache" "$python_bin" -m py_compile \
  info-track/ai-news/scripts/ai_news.py \
  info-track/ai-news/scripts/adapters/__init__.py \
  info-track/ai-news/scripts/adapters/common.py \
  info-track/ai-news/scripts/adapters/rss.py \
  info-track/ai-news/scripts/adapters/json_api.py \
  info-track/ai-news/scripts/adapters/html_index.py \
  openclaw-skills/tts/scripts/volc_tts.py \
  openclaw-skills/stt/scripts/volc_stt.py \
  openclaw-skills/image-gen/scripts/volc_image_gen.py \
  openclaw-skills/video-gen/scripts/volc_video_gen.py \
  openclaw-skills/volc-search/scripts/web_search.py

"$python_bin" info-track/ai-news/scripts/ai_news.py --help >/dev/null
"$python_bin" info-track/ai-news/scripts/ai_news.py validate --input info-track/ai-news/references/example-candidates.json >/dev/null
"$python_bin" info-track/ai-news/scripts/ai_news.py collect --dry-run --date 2026-06-27 >/dev/null
"$python_bin" info-track/ai-news/scripts/ai_news.py render --input info-track/ai-news/references/example-candidates.json >/dev/null
"$python_bin" info-track/ai-news/scripts/ai_news.py run --dry-run --date 2026-06-27 >/dev/null

if command -v uv >/dev/null 2>&1; then
  uv lock --check >/dev/null
else
  fail "uv is required to verify locked Python dependencies"
fi

if rg -n 'build-skill-bundle|cli/macos|cli/linux|volc-websearch|volc-gen/|volc-speech/|my-fetch/' README.md AGENTS.md docs/OPENCLAW-SKILL.md openclaw-skills info-track; then
  fail "new docs should not reference removed Rust/CLI skill paths"
fi

if rg -n 'Tavily|Bocha|Brave|tavily|bocha|brave|TORCHLIGHT_API_KEY|api-key|VeFaaS|vefaas|VE_ACCESS_KEY|VE_SECRET_KEY|setup-guide|多引擎|multi-engine' openclaw-skills/volc-search README.md AGENTS.md; then
  fail "volc-search must use only Volcengine WebSearch"
fi

pass "repository structure and skill files verified"
