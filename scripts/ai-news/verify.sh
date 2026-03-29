#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common.sh
source "$SCRIPT_DIR/../common.sh"

if [[ "${1:-}" == "--live" ]]; then
  LIVE_MODE=1
fi

AI_NEWS_DIR="$ROOT_DIR/ai-news"

section "ai-news"

assert_file_exists "$AI_NEWS_DIR/SKILL.md" "ai-news SKILL.md exists"
assert_file_exists "$AI_NEWS_DIR/sources.md" "ai-news sources.md exists"
assert_file_exists "$AI_NEWS_DIR/format.md" "ai-news format.md exists"

if rg -q '^metadata: \{.*\}$' "$AI_NEWS_DIR/SKILL.md"; then
  pass "metadata is single-line JSON"
else
  fail "metadata must be single-line JSON"
fi

assert_contains "$AI_NEWS_DIR/SKILL.md" "name: ai-news" "skill name is ai-news"
assert_contains "$AI_NEWS_DIR/SKILL.md" "[sources.md](sources.md)" "SKILL.md references sources.md"
assert_contains "$AI_NEWS_DIR/SKILL.md" "[format.md](format.md)" "SKILL.md references format.md"
assert_contains "$AI_NEWS_DIR/SKILL.md" "24-48 小时" "SKILL.md documents default 24-48 hour window"
assert_contains "$AI_NEWS_DIR/SKILL.md" "## 工作流" "SKILL.md focuses on workflow"
assert_contains "$AI_NEWS_DIR/SKILL.md" "默认使用最通用的 \`web_search\` 和 \`web_fetch\`" "SKILL.md prefers generic tools"
assert_contains "$AI_NEWS_DIR/SKILL.md" "没有先读 \`sources.md\`，不要开始抓取" "SKILL.md requires reading sources before fetching"
assert_contains "$AI_NEWS_DIR/SKILL.md" "没有先读 \`format.md\`，不要开始写结果" "SKILL.md requires reading format before writing"
assert_contains "$AI_NEWS_DIR/SKILL.md" "### 5. 成稿前重新读 format.md" "SKILL.md forces format.md reread before writing"
assert_contains "$AI_NEWS_DIR/SKILL.md" "先回到 [sources.md](sources.md) 查对应的访问说明、权重和替代入口" "SKILL.md sends runtime source decisions back to sources.md"
assert_contains "$AI_NEWS_DIR/SKILL.md" "至少覆盖 \`tavily\`、\`bocha\`" "SKILL.md requires tavily and bocha coverage"
assert_contains "$AI_NEWS_DIR/SKILL.md" "\`brave\`" "SKILL.md includes brave for English verification"
assert_contains "$AI_NEWS_DIR/sources.md" "## 官方一级优先源矩阵" "sources document starts from official priority matrix"
assert_contains "$AI_NEWS_DIR/sources.md" "## 搜索引擎分工" "sources documents search engine roles"
assert_contains "$AI_NEWS_DIR/sources.md" "https://maomu.com/news" "sources include maomu"
assert_contains "$AI_NEWS_DIR/sources.md" "https://ai.hubtoday.app/" "sources include hubtoday"
assert_contains "$AI_NEWS_DIR/sources.md" "OpenAI" "sources include OpenAI official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "Anthropic" "sources include Anthropic official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "Google AI / DeepMind" "sources include Google official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "xAI" "sources include xAI official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "MiniMax" "sources include MiniMax official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "智谱 AI" "sources include Zhipu official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "Kimi / Moonshot" "sources include Kimi official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "阿里 AI" "sources include Alibaba official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "腾讯 AI" "sources include Tencent official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "火山引擎" "sources include Volcengine official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "Manus" "sources include Manus official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "### Tavily" "sources define Tavily role"
assert_contains "$AI_NEWS_DIR/sources.md" "### Bocha" "sources define Bocha role"
assert_contains "$AI_NEWS_DIR/sources.md" "### Brave" "sources define Brave role"
assert_contains "$AI_NEWS_DIR/format.md" "## 大模型" "format defines categories"
assert_contains "$AI_NEWS_DIR/format.md" "发布时间" "format requires published time"
assert_contains "$AI_NEWS_DIR/format.md" "来源链接" "format requires source link"

if ! need_live; then
  skip "live source checks disabled; run with --live to verify source URLs"
  exit 0
fi

urls=(
  "https://www.theverge.com/ai-artificial-intelligence"
  "https://www.wired.com/feed/tag/ai/latest/rss"
  "https://techcrunch.com/feed/"
  "https://www.anthropic.com/news"
  "https://www.technologyreview.com/feed/"
  "https://blog.google/innovation-and-ai/technology/ai/"
  "https://maomu.com/news"
  "https://ai.hubtoday.app/"
)

for url in "${urls[@]}"; do
  info "checking $url"
  if curl -L --fail --silent --show-error --max-time 20 -A "Mozilla/5.0" -o /dev/null "$url"; then
    pass "$url is reachable"
  else
    fail "$url is not reachable"
  fi
done
