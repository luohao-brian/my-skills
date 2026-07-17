#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/my-skills-pycache"

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
  openclaw-skills/ark-tts
  openclaw-skills/ark-stt
  openclaw-skills/ark-image-gen
  openclaw-skills/ark-video-gen
  openclaw-skills/ark-vision
  openclaw-skills/ark-search
  openclaw-skills/ark-data-pro
  openclaw-skills/volc-search
  openclaw-skills/popular-web-designs
  openclaw-skills/guizang-ppt-skill
  openclaw-skills/ppt-master
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
assert_file openclaw-skills/volc-search/requirements.txt
assert_contains openclaw-skills/volc-search/requirements.txt "requests>=2.32,<3"
assert_file openclaw-skills/ark-search/requirements.txt
assert_contains openclaw-skills/ark-search/requirements.txt "requests>=2.32,<3"
assert_file openclaw-skills/ark-vision/requirements.txt
assert_contains openclaw-skills/ark-vision/requirements.txt "requests>=2.32,<3"
assert_file openclaw-skills/ark-data-pro/requirements.txt
assert_contains openclaw-skills/ark-data-pro/requirements.txt "requests>=2.32,<3"

assert_contains openclaw-skills/ark-tts/SKILL.md "references/ark-tts.md"
assert_contains openclaw-skills/ark-stt/SKILL.md "references/ark-stt.md"
assert_contains openclaw-skills/ark-image-gen/SKILL.md "references/ark-image-gen.md"
assert_contains openclaw-skills/ark-video-gen/SKILL.md "references/ark-video-gen.md"
assert_contains openclaw-skills/ark-vision/SKILL.md "references/ark-vision.md"
assert_contains openclaw-skills/ark-vision/SKILL.md "ARK_AGENT_PLAN_API_KEY"
assert_contains openclaw-skills/ark-vision/SKILL.md "vision_analyze.py"
assert_contains openclaw-skills/ark-search/SKILL.md "references/docs-index.md"
assert_contains openclaw-skills/ark-search/SKILL.md "ARK_AGENT_PLAN_API_KEY"
assert_contains openclaw-skills/ark-data-pro/SKILL.md "references/docs-index.md"
assert_contains openclaw-skills/ark-data-pro/SKILL.md "ARK_AGENT_PLAN_API_KEY"
assert_contains openclaw-skills/ark-data-pro/SKILL.md "data_pro_search.py"
assert_contains openclaw-skills/volc-search/SKILL.md "references/docs-index.md"
assert_contains openclaw-skills/volc-search/SKILL.md "融合信息搜索"
assert_contains openclaw-skills/popular-web-designs/SKILL.md "references/catalog.md"
assert_contains openclaw-skills/popular-web-designs/SKILL.md "templates/<site>.md"
assert_file openclaw-skills/guizang-ppt-skill/LICENSE
assert_file openclaw-skills/guizang-ppt-skill/assets/template.html
assert_file openclaw-skills/guizang-ppt-skill/assets/template-swiss.html
assert_file openclaw-skills/guizang-ppt-skill/assets/swiss-golden.html
assert_file openclaw-skills/guizang-ppt-skill/templates/swiss-golden-slides.html
assert_file openclaw-skills/guizang-ppt-skill/references/swiss-contract.json
assert_file openclaw-skills/guizang-ppt-skill/scripts/create-deck.mjs
assert_file openclaw-skills/guizang-ppt-skill/scripts/validate-swiss-deck.mjs
assert_file openclaw-skills/guizang-ppt-skill/scripts/verify-swiss-contract.mjs
assert_file openclaw-skills/guizang-ppt-skill/scripts/visual-check-swiss.mjs
assert_contains openclaw-skills/guizang-ppt-skill/SKILL.md "references/swiss-contract.json"
assert_contains openclaw-skills/guizang-ppt-skill/SKILL.md "scripts/validate-swiss-deck.mjs"
assert_contains openclaw-skills/guizang-ppt-skill/assets/template-swiss.html "<!-- SLIDES_START -->"
assert_contains openclaw-skills/guizang-ppt-skill/assets/template-swiss.html "<!-- SLIDES_END -->"
assert_contains openclaw-skills/guizang-ppt-skill/assets/template.html "<!-- SLIDES_START -->"
assert_contains openclaw-skills/guizang-ppt-skill/assets/template.html "<!-- SLIDES_END -->"
if rg -n --glob '*.md' 'GPT-M 2\.0|CleanShot X|Claude Code|Codex|Ask Question|ask_question|CLAUDE\.md|CodePilot|Fujifilm|Leica|Runtime Capability Contract|结构化用户询问|显著改变结果' openclaw-skills/guizang-ppt-skill; then
  fail "guizang-ppt-skill instructions must stay concrete and product-neutral"
fi
assert_file openclaw-skills/ppt-master/LICENSE
assert_file openclaw-skills/ppt-master/references/openclaw-runtime.md
assert_file openclaw-skills/ppt-master/references/upstream-source.md
assert_file openclaw-skills/ppt-master/references/upstream-pipeline.md
assert_file openclaw-skills/ppt-master/scripts/visual_layout_audit.py
assert_file openclaw-skills/ppt-master/scripts/pptx_layout_audit.py
assert_file openclaw-skills/ppt-master/scripts/image_manifest.py
assert_file openclaw-skills/ppt-master/scripts/audio_manifest.py
assert_no_path openclaw-skills/ppt-master/scripts/image_gen.py
assert_no_path openclaw-skills/ppt-master/scripts/notes_to_audio.py
assert_no_path openclaw-skills/ppt-master/scripts/image_backends
assert_no_path openclaw-skills/ppt-master/scripts/tts_backends
assert_contains openclaw-skills/ppt-master/SKILL.md "scripts/visual_layout_audit.py"
assert_contains openclaw-skills/ppt-master/SKILL.md "scripts/pptx_layout_audit.py"
assert_contains openclaw-skills/ppt-master/SKILL.md "--dir <absolute-projects-root>"
if rg -n --glob '*.md' --glob '*.py' --glob '*.json' --glob '!templates/**' \
  'Claude Code|Codex|Antigravity|Hermes|My Cowork|ask_question|TeamCreate|SendMessage|~/.agents|CLAUDE\.md|Cursor|Codebuddy|VS Code \+ Copilot|playwright MCP|Runtime Capability Contract|结构化用户询问|显著改变结果' \
  openclaw-skills/ppt-master; then
  fail "ppt-master instructions must stay concrete and product-neutral"
fi
if find openclaw-skills/ppt-master -type f -iname 'README.md' -print -quit | rg -q .; then
  fail "ppt-master must not contain README.md files"
fi
if find openclaw-skills/ppt-master -type d -name '__pycache__' -print -quit | rg -q .; then
  fail "ppt-master must not contain __pycache__ directories"
fi
if rg -n --glob '!**/templates/**' --glob '!references/upstream-source.md' \
  'IMAGE_BACKEND|image_gen\.py|notes_to_audio\.py|scripts/(image|tts)_backends|edge-tts|ElevenLabs|CosyVoice' \
  openclaw-skills/ppt-master; then
  fail "ppt-master image and narration generation must use runtime tools only"
fi
popular_template_count="$(find openclaw-skills/popular-web-designs/templates -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')"
[[ "$popular_template_count" == "54" ]] || fail "popular-web-designs should include 54 templates, found $popular_template_count"
if rg -n 'Hermes|write_file|generative-widgets|browser_vision|cloudflared|skill_view|claude-design|design-md|DESIGN\.md|metadata\.hermes|triggers:' openclaw-skills/popular-web-designs; then
  fail "popular-web-designs must stay decoupled from Hermes/runtime-specific skill contracts"
fi

assert_file info-track/ai-news/references/sources.json
assert_file info-track/ai-news/references/output-schema.md
assert_file info-track/ai-news/references/brief-format.md
assert_no_path info-track/ai-news/format.md
assert_no_path info-track/ai-news/sources.md
assert_no_path info-track/ai-news/references/source-contract.md
assert_no_path info-track/ai-news/references/brief-rules.md
assert_no_path info-track/ai-news/templates/brief.md.tpl
assert_no_path info-track/ai-news/templates/item.md.tpl
assert_file info-track/ai-news/scripts/ai_news.py
assert_file info-track/ai-news/scripts/adapters/__init__.py
assert_contains info-track/ai-news/SKILL.md "scripts/ai_news.py collect"
assert_contains info-track/ai-news/SKILL.md "scripts/ai_news.py render"
assert_contains info-track/ai-news/SKILL.md "references/sources.json"
assert_contains info-track/ai-news/SKILL.md '`title`、`url`、`summary`'
assert_contains info-track/ai-news/SKILL.md "## 来源与候选"
assert_contains info-track/ai-news/SKILL.md "## 成稿规则"

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
  openclaw-skills/ark-tts/scripts/volc_tts.py \
  openclaw-skills/ark-stt/scripts/volc_stt.py \
  openclaw-skills/ark-image-gen/scripts/volc_image_gen.py \
  openclaw-skills/ark-video-gen/scripts/volc_video_gen.py \
  openclaw-skills/ark-vision/scripts/vision_analyze.py \
  openclaw-skills/ark-search/scripts/web_search.py \
  openclaw-skills/ark-data-pro/scripts/data_pro_search.py \
  openclaw-skills/volc-search/scripts/web_search.py \
  openclaw-skills/ppt-master/scripts/image_manifest.py \
  openclaw-skills/ppt-master/scripts/audio_manifest.py \
  openclaw-skills/ppt-master/scripts/audio_duration.py \
  openclaw-skills/ppt-master/scripts/image_download.py \
  openclaw-skills/ppt-master/scripts/visual_layout_audit.py \
  openclaw-skills/ppt-master/scripts/pptx_layout_audit.py

"$python_bin" openclaw-skills/ark-vision/scripts/vision_analyze.py --help >/dev/null
"$python_bin" openclaw-skills/ark-data-pro/scripts/data_pro_search.py --help >/dev/null
"$python_bin" info-track/ai-news/scripts/ai_news.py --help >/dev/null
"$python_bin" openclaw-skills/ppt-master/scripts/visual_layout_audit.py --help >/dev/null
"$python_bin" openclaw-skills/ppt-master/scripts/pptx_layout_audit.py --help >/dev/null
"$python_bin" openclaw-skills/ppt-master/scripts/image_manifest.py --help >/dev/null
"$python_bin" openclaw-skills/ppt-master/scripts/audio_manifest.py --help >/dev/null
ai_news_verify_dir="$(mktemp -d "${TMPDIR:-/tmp}/ai-news-verify.XXXXXX")"
trap 'rm -rf "$ai_news_verify_dir"' EXIT
"$python_bin" info-track/ai-news/scripts/ai_news.py verify-sources --window 72h --out "$ai_news_verify_dir/candidates.json"
"$python_bin" info-track/ai-news/scripts/ai_news.py validate --input "$ai_news_verify_dir/candidates.json" >/dev/null
"$python_bin" info-track/ai-news/scripts/ai_news.py render --input "$ai_news_verify_dir/candidates.json" >"$ai_news_verify_dir/brief.md"
[[ -s "$ai_news_verify_dir/brief.md" ]] || fail "ai-news live render produced an empty brief"
if rg -n '^\[ai-news\]|^ERROR:|Traceback|Article URL:|Comments URL:|Points:' "$ai_news_verify_dir/brief.md"; then
  fail "ai-news live markdown contains logs, tracebacks, or uncleaned aggregator fields"
fi

if command -v uv >/dev/null 2>&1; then
  uv lock --check >/dev/null
else
  fail "uv is required to verify locked Python dependencies"
fi

if command -v node >/dev/null 2>&1; then
  node --check "$ROOT_DIR/openclaw-skills/guizang-ppt-skill/scripts/visual-check-swiss.mjs"
  node "$ROOT_DIR/openclaw-skills/guizang-ppt-skill/scripts/build-swiss-golden.mjs" --check
  node "$ROOT_DIR/openclaw-skills/guizang-ppt-skill/scripts/verify-swiss-contract.mjs"
  node "$ROOT_DIR/openclaw-skills/guizang-ppt-skill/scripts/validate-swiss-deck.mjs" \
    "$ROOT_DIR/openclaw-skills/guizang-ppt-skill/assets/swiss-golden.html"
else
  fail "node is required to verify guizang-ppt-skill"
fi

if rg -n 'build-skill-bundle|cli/macos|cli/linux|volc-websearch|volc-gen/|volc-speech/|my-fetch/' README.md AGENTS.md docs/OPENCLAW-SKILL.md openclaw-skills info-track; then
  fail "new docs should not reference removed Rust/CLI skill paths"
fi

if rg -n 'Tavily|Bocha|Brave|tavily|bocha|brave|TORCHLIGHT_API_KEY|api-key|VeFaaS|vefaas|VE_ACCESS_KEY|VE_SECRET_KEY|setup-guide|多引擎|multi-engine' openclaw-skills/volc-search README.md AGENTS.md; then
  fail "volc-search must use only Volcengine WebSearch"
fi

pass "repository structure and skill files verified"
