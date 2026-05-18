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
assert_contains "$AI_NEWS_DIR/SKILL.md" "没有先读 \`sources.md\`，不要开始收集来源" "SKILL.md requires reading sources before collecting"
assert_contains "$AI_NEWS_DIR/SKILL.md" "没有先读 \`format.md\`，不要开始写结果" "SKILL.md requires reading format before writing"
assert_contains "$AI_NEWS_DIR/SKILL.md" "成稿前再读一遍 [format.md](format.md)" "SKILL.md forces format.md reread before writing"
assert_contains "$AI_NEWS_DIR/SKILL.md" "不要把全部召回候选都发起逐条字段核对任务" "SKILL.md avoids full-candidate field validation"
assert_contains "$AI_NEWS_DIR/SKILL.md" "## Agent 边界" "SKILL.md defines agent boundaries"
assert_contains "$AI_NEWS_DIR/SKILL.md" "不要对 [sources.md](sources.md) 中的固定来源做可信度排序、剔除、替换或维护决策" "SKILL.md forbids source maintenance decisions"
assert_contains "$AI_NEWS_DIR/SKILL.md" "不要判断固定来源内容的真伪；只检查字段是否满足成稿要求" "SKILL.md limits source checks to data fields"
assert_contains "$AI_NEWS_DIR/SKILL.md" "候选集应覆盖中文来源、英文来源、官方发布入口和技术来源" "SKILL.md requires broad source coverage"
assert_contains "$AI_NEWS_DIR/SKILL.md" "记录来源不可用或候选字段不完整" "SKILL.md reports unavailable sources and incomplete fields"
assert_contains "$AI_NEWS_DIR/SKILL.md" "是否先筛选候选，再只核对准备入稿条目的必要字段" "SKILL.md checks candidate filtering before field validation"
assert_contains "$AI_NEWS_DIR/sources.md" "## 官网 / 官方发布入口" "sources document starts from official entry points"
assert_contains "$AI_NEWS_DIR/sources.md" "## 来源数据边界" "sources documents source data boundaries"
assert_contains "$AI_NEWS_DIR/sources.md" "https://maomu.com/news" "sources include maomu"
assert_contains "$AI_NEWS_DIR/sources.md" "https://hex2077.dev/" "sources include hubtoday redirect target"
assert_contains "$AI_NEWS_DIR/sources.md" "OpenAI" "sources include OpenAI official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "Anthropic" "sources include Anthropic official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "Google AI / Gemini / DeepMind" "sources include Google official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "xAI" "sources include xAI official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "MiniMax" "sources include MiniMax official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "智谱 AI" "sources include Zhipu official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "Kimi / Moonshot" "sources include Kimi official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "阿里 AI" "sources include Alibaba official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "腾讯 AI" "sources include Tencent official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "火山引擎" "sources include Volcengine official priority"
assert_contains "$AI_NEWS_DIR/sources.md" "### 来源覆盖" "sources define source coverage"
assert_contains "$AI_NEWS_DIR/sources.md" "### 官方来源" "sources define official source rules"
assert_contains "$AI_NEWS_DIR/sources.md" "### 社区和聚合入口" "sources define community and aggregation boundaries"
assert_contains "$AI_NEWS_DIR/sources.md" "## 来源数据预期" "sources include source data expectations"
assert_contains "$AI_NEWS_DIR/sources.md" "来源入口默认可信；执行时只检查数据字段是否满足成稿要求，不判断来源真伪" "sources define trusted-entry consumer boundary"
assert_contains "$AI_NEWS_DIR/sources.md" "官方发布页、官方博客、官方文档、GitHub Release、模型页和论文页应提供标题、URL、发布时间或版本发布时间" "sources define official source data shape"
assert_contains "$AI_NEWS_DIR/sources.md" "社区入口和聚合入口应提供标题、URL、展示时间或讨论时间、线索摘要" "sources define community and aggregation data shape"
assert_contains "$AI_NEWS_DIR/format.md" "## 大模型" "format defines categories"
assert_contains "$AI_NEWS_DIR/format.md" "发布时间" "format requires published time"
assert_contains "$AI_NEWS_DIR/format.md" "来源链接" "format requires source link"

if rg -q 'bocha|brave|tavily|volc-websearch|搜索引擎分工|检索入口分工|抓取失败策略|来源补漏边界|官方回源|当前来源质量评估|不稳定入口|固定来源清单|来源质量|正文支撑|用 `tavily`' "$AI_NEWS_DIR/SKILL.md" "$AI_NEWS_DIR/sources.md" "$ROOT_DIR/README_AI_NEWS.md"; then
  fail "ai-news docs must not prescribe search engine or tool fallback behavior"
else
  pass "ai-news docs do not prescribe search engine or tool fallback behavior"
fi

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
  "https://maomu.com/news"
  "https://hex2077.dev/"
)

for url in "${urls[@]}"; do
  info "checking $url"
  if curl -L --fail --silent --show-error --max-time 20 -A "Mozilla/5.0" -o /dev/null "$url"; then
    pass "$url is reachable"
  else
    fail "$url is not reachable"
  fi
done
