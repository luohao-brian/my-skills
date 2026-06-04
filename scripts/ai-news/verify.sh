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
assert_contains "$AI_NEWS_DIR/SKILL.md" "最近 \`72\` 小时" "SKILL.md documents default 72 hour window"
assert_contains "$AI_NEWS_DIR/SKILL.md" "## 工作流" "SKILL.md focuses on workflow"
assert_contains "$AI_NEWS_DIR/SKILL.md" "没有先读 \`sources.md\`，不要开始收集来源" "SKILL.md requires reading sources before collecting"
assert_contains "$AI_NEWS_DIR/SKILL.md" "没有先读 \`format.md\`，不要开始写结果" "SKILL.md requires reading format before writing"
assert_contains "$AI_NEWS_DIR/SKILL.md" "成稿前再读一遍 [format.md](format.md)" "SKILL.md forces format.md reread before writing"
assert_contains "$AI_NEWS_DIR/SKILL.md" "先按时间窗、AI 相关性和重复事件筛选候选，再核对入稿字段" "SKILL.md avoids full-candidate field validation"
assert_contains "$AI_NEWS_DIR/SKILL.md" "## Agent 边界" "SKILL.md defines agent boundaries"
assert_contains "$AI_NEWS_DIR/SKILL.md" "不要对 [sources.md](sources.md) 中的固定来源做可信度排序、剔除、替换或维护决策" "SKILL.md forbids source maintenance decisions"
assert_contains "$AI_NEWS_DIR/SKILL.md" "不要判断固定来源内容的真伪；只检查字段是否满足成稿要求" "SKILL.md limits source checks to data fields"
assert_contains "$AI_NEWS_DIR/SKILL.md" "读取 [sources.md](sources.md) 的日报扫描入口" "SKILL.md uses daily scan sources"
assert_contains "$AI_NEWS_DIR/SKILL.md" "只使用 [sources.md](sources.md) 列出的入口" "SKILL.md only uses listed sources"
assert_contains "$AI_NEWS_DIR/SKILL.md" "不为了补数量扩展来源范围" "SKILL.md avoids quantity-driven expansion"
assert_contains "$AI_NEWS_DIR/SKILL.md" "任务范围包含官网、官博或技术博客内容时，只按 [sources.md](sources.md) 的定向取数入口取数" "SKILL.md uses targeted source entries without expansion"
assert_contains "$AI_NEWS_DIR/SKILL.md" "Feed、列表页、日期页或聚合页字段完整时可以直接成稿" "SKILL.md allows complete feed, list, date, and aggregation pages as final sources"
assert_contains "$AI_NEWS_DIR/SKILL.md" "记录来源不可用或候选字段不完整" "SKILL.md reports unavailable sources and incomplete fields"
assert_contains "$AI_NEWS_DIR/SKILL.md" "是否先筛选候选，再核对入稿字段" "SKILL.md checks candidate filtering before field validation"
assert_contains "$AI_NEWS_DIR/SKILL.md" "## 分类容量" "SKILL.md defines category capacity"
assert_contains "$AI_NEWS_DIR/SKILL.md" "模型 / 研究：18-28 条" "SKILL.md sets model and research capacity"
assert_contains "$AI_NEWS_DIR/SKILL.md" "Agent / 开发者工具：12-20 条" "SKILL.md sets agent and developer tooling capacity"
assert_contains "$AI_NEWS_DIR/SKILL.md" "技术博客 / 工程实践：6-10 条" "SKILL.md sets technical blog and engineering capacity"
assert_contains "$AI_NEWS_DIR/SKILL.md" "产品 / 应用：18-30 条" "SKILL.md sets product and application capacity"
assert_contains "$AI_NEWS_DIR/SKILL.md" "商业 / 融资：4-7 条" "SKILL.md sets business and funding capacity"
assert_contains "$AI_NEWS_DIR/SKILL.md" "安全 / 治理：6-10 条" "SKILL.md sets safety and governance capacity"
assert_contains "$AI_NEWS_DIR/SKILL.md" "以下区间只控制篇幅，未超上限不压缩" "SKILL.md treats category range as size limit"
assert_contains "$AI_NEWS_DIR/SKILL.md" "不要把同一主题下的不同产品、模型、论文、功能、融资或治理事件综合成一条" "SKILL.md prevents over-compression by topic synthesis"
assert_contains "$AI_NEWS_DIR/SKILL.md" "综合新闻和聚合入口本身已经做过一定筛选，字段完整的独立条目应按条保留" "SKILL.md preserves complete independent aggregation items"
assert_contains "$AI_NEWS_DIR/SKILL.md" "同一主题下的不同进展不要合并成一条" "SKILL.md narrows deduplication scope"
assert_contains "$AI_NEWS_DIR/SKILL.md" "是否按分类容量输出有效候选，并避免把同主题不同进展综合成一条" "SKILL.md checklist guards category capacity"
assert_contains "$AI_NEWS_DIR/SKILL.md" "## 低 fetch 低失真" "SKILL.md defines low-fetch low-distortion drafting"
assert_contains "$AI_NEWS_DIR/SKILL.md" "字段完整的入口条目可以直接入稿，不因未读取详情页而删除" "SKILL.md preserves complete source entries without detail reads"
assert_contains "$AI_NEWS_DIR/SKILL.md" "不通过继续读取详情页来补容量" "SKILL.md does not add detail fetches for capacity"
assert_contains "$AI_NEWS_DIR/SKILL.md" "是否避免把分类区间当作压缩目标" "SKILL.md checklist guards against range compression"
assert_contains "$AI_NEWS_DIR/sources.md" "## 日报扫描入口" "sources define daily scan entries"
assert_contains "$AI_NEWS_DIR/sources.md" "### 新闻 Feed" "sources define news feed entries"
assert_contains "$AI_NEWS_DIR/sources.md" "### 英文聚合 Feed" "sources define English aggregation feed entries"
assert_contains "$AI_NEWS_DIR/sources.md" "### 中文聚合页" "sources define Chinese aggregation entries"
assert_contains "$AI_NEWS_DIR/sources.md" "## 定向取数入口" "sources define targeted source entries"
assert_contains "$AI_NEWS_DIR/sources.md" "按列出的页面和字段取数" "sources keep targeted entries field-oriented"
assert_contains "$AI_NEWS_DIR/sources.md" "不要把这些入口扩展成未列页面、厂商矩阵或额外来源" "sources forbid expanding targeted entries"
assert_contains "$AI_NEWS_DIR/sources.md" "## 官网和技术博客入口" "sources keep official and technical blog entries"
assert_contains "$AI_NEWS_DIR/sources.md" "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml" "sources use The Verge AI RSS"
assert_contains "$AI_NEWS_DIR/sources.md" "https://techcrunch.com/category/artificial-intelligence/feed/" "sources use TechCrunch AI RSS"
assert_contains "$AI_NEWS_DIR/sources.md" "https://tensorfeed.ai/api/news" "sources include TensorFeed JSON"
assert_contains "$AI_NEWS_DIR/sources.md" "https://www.dailydoseofai.tech/rss.xml" "sources include AI Dose RSS"
assert_contains "$AI_NEWS_DIR/sources.md" "https://planet-ai.net/rss.xml" "sources include Planet AI RSS"
assert_contains "$AI_NEWS_DIR/sources.md" "只有 \`Article URL\` / \`Comments URL\` / \`Points\` 时不满足摘要字段" "sources document TensorFeed metadata-only snippets"
assert_contains "$AI_NEWS_DIR/sources.md" "https://www.tmtpost.com/user/7944025" "sources include TMT Edge AI Daily"
assert_contains "$AI_NEWS_DIR/sources.md" "详情页 \`<blockquote>\` 小节可拆成多条新闻" "sources document TMT blockquote item extraction"
assert_contains "$AI_NEWS_DIR/sources.md" "https://maomu.com/news" "sources include maomu"
assert_contains "$AI_NEWS_DIR/sources.md" "优先读取页面嵌入的结构化对象" "sources document maomu structured extraction"
assert_contains "$AI_NEWS_DIR/sources.md" "https://daily.xiaohu.ai/" "sources include Xiaohu daily"
assert_contains "$AI_NEWS_DIR/sources.md" "https://hex2077.dev/docs/" "sources include Hex2077 daily docs"
assert_contains "$AI_NEWS_DIR/sources.md" "https://daily.xiaohu.ai/YYYY-MM-DD/" "sources document Xiaohu date page pattern"
assert_contains "$AI_NEWS_DIR/sources.md" "https://hex2077.dev/docs/YYYY-MM/YYYY-MM-DD/" "sources document Hex2077 date page pattern"
assert_contains "$AI_NEWS_DIR/sources.md" "按标题和摘要区块配对" "sources document Xiaohu title summary pairing"
assert_contains "$AI_NEWS_DIR/sources.md" "拆不到独立条目时，使用页面 title / description 成稿一条" "sources document Hex2077 fallback item"
assert_contains "$AI_NEWS_DIR/sources.md" "剔除非公开文章链接、无效摘要、消费品 / 电商噪音" "sources document Chinese source screening"
assert_contains "$AI_NEWS_DIR/sources.md" "https://openai.com/news/rss.xml" "sources include OpenAI RSS entry"
assert_contains "$AI_NEWS_DIR/sources.md" "https://www.anthropic.com/news" "sources include Anthropic official entry"
assert_contains "$AI_NEWS_DIR/sources.md" "https://www.anthropic.com/engineering" "sources include Anthropic engineering entry"
assert_contains "$AI_NEWS_DIR/sources.md" "只收录摘要内容存在的条目" "sources document Anthropic summary constraint"
assert_contains "$AI_NEWS_DIR/sources.md" "https://blog.google/innovation-and-ai/technology/ai/rss/" "sources include Google AI RSS entry"
assert_contains "$AI_NEWS_DIR/sources.md" "https://deepmind.google/blog/rss.xml" "sources include DeepMind RSS entry"
assert_contains "$AI_NEWS_DIR/sources.md" "https://www.interconnects.ai/feed" "sources include Interconnects technical feed"
assert_contains "$AI_NEWS_DIR/sources.md" "## 入稿字段" "sources include field expectations"
assert_contains "$AI_NEWS_DIR/sources.md" "入口页、Feed、JSON 或日期页的解码后内容中直接提供标题" "sources require field-friendly decoded source surfaces"
assert_contains "$AI_NEWS_DIR/sources.md" "只给标题或只给跳转链接的聚合入口不放进扫描入口" "sources exclude aggregation pages without summary fields"
assert_contains "$AI_NEWS_DIR/sources.md" "日期页型入口的目标日期页不存在时，可以使用目标日期前后 \`72\` 小时内最近的已发布日期页建立候选" "sources allow nearby date pages for date-page sources"
assert_contains "$AI_NEWS_DIR/sources.md" "入稿仍按条目的发布时间、页面日期和目标时间窗筛选" "sources keep time window strict when using nearby date pages"
assert_contains "$AI_NEWS_DIR/sources.md" "没有单条原文链接时可使用聚合日期页链接" "sources allow date pages as final source links when needed"
assert_contains "$AI_NEWS_DIR/SKILL.md" "- 模型 / 研究" "SKILL.md defines model and research category"
assert_contains "$AI_NEWS_DIR/SKILL.md" "- Agent / 开发者工具" "SKILL.md defines agent and developer tooling category"
assert_contains "$AI_NEWS_DIR/SKILL.md" "- 技术博客 / 工程实践" "SKILL.md defines technical blog and engineering practice category"
assert_contains "$AI_NEWS_DIR/SKILL.md" "- 产品 / 应用" "SKILL.md defines product and application category"
assert_contains "$AI_NEWS_DIR/SKILL.md" "- 商业 / 融资" "SKILL.md defines business and funding category"
assert_contains "$AI_NEWS_DIR/SKILL.md" "- 安全 / 治理" "SKILL.md defines safety and governance category"
assert_contains "$AI_NEWS_DIR/format.md" "## 🧠 模型 / 研究" "format defines model and research category"
assert_contains "$AI_NEWS_DIR/format.md" "## 🛠️ Agent / 开发者工具" "format defines agent and developer tooling category"
assert_contains "$AI_NEWS_DIR/format.md" "## 🧪 技术博客 / 工程实践" "format defines technical blog and engineering practice category"
assert_contains "$AI_NEWS_DIR/format.md" "## 🚀 产品 / 应用" "format defines product and application category"
assert_contains "$AI_NEWS_DIR/format.md" "## 💼 商业 / 融资" "format defines business and funding category"
assert_contains "$AI_NEWS_DIR/format.md" "## 🛡️ 安全 / 治理" "format defines safety and governance category"
assert_contains "$AI_NEWS_DIR/format.md" "分类用二级标题，标题固定带 emoji" "format requires category emoji headings"
assert_contains "$AI_NEWS_DIR/format.md" "## 排版规则" "format focuses on presentation rules"
assert_contains "$AI_NEWS_DIR/format.md" "发布时间" "format requires published time"
assert_contains "$AI_NEWS_DIR/format.md" "来源链接" "format requires source link"

if rg -q '时间窗|只保留|覆盖不足|字段完整|来源提供|聚合日期页|重要性排序|候选|不要求严格按时间倒序' "$AI_NEWS_DIR/format.md"; then
  fail "format.md must not duplicate source, screening, or workflow rules"
else
  pass "format.md only describes output structure and presentation"
fi

if rg -q 'bocha|brave|tavily|volc-websearch|搜索引擎分工|检索入口分工|抓取失败策略|来源补漏边界|官方回源|当前来源质量评估|不稳定入口|固定来源清单|来源质量|正文支撑|用 `tavily`|每次都覆盖|每次日报都要|候选集应覆盖中文来源|官方发布入口和技术来源|至少覆盖 Hugging Face|至少使用一个官方来源|重点品牌是否使用|追官方|回源原则|详情页和回源|按需入口|用户点名' "$AI_NEWS_DIR/SKILL.md" "$AI_NEWS_DIR/sources.md" "$AI_NEWS_DIR/format.md" "$ROOT_DIR/README_AI_NEWS.md"; then
  fail "ai-news docs must not prescribe search engine behavior or old full-matrix coverage"
else
  pass "ai-news docs do not prescribe search engine behavior or old full-matrix coverage"
fi

if rg -q 'github.com|qwenlm.github.io|help.openai.com/en/articles/9624314|help.openai.com/en/articles/6825453-chatgpt-release-notes|https://x.ai/|https://grok.com/|https://moonshot.cn/|https://deepseek.com/|https://cloud.tencent.com/document/product/1729/104753|https://openai.com/news/product/|https://openai.com/news/research/|https://openai.com/news/engineering/|https://blog.google/innovation-and-ai/technology/ai/`|https://deepmind.google/blog/`|https://www.minimax.io/news|https://www.zhipuai.cn/zh/news|https://www.zhipuai.cn/zh/research|https://developer.volcengine.com/articles|https://huggingface.co/blog/feed.xml|www.littleworld.win|aggyai.com|clawdigest.live|bensbites.com|chatbotnews.ai|ainewshub.io|ainewsguru.com|rundown.ai' "$AI_NEWS_DIR/sources.md"; then
  fail "sources must not include stale official entries or GitHub organization sources"
else
  pass "sources exclude stale official entries, noisy aggregators, and GitHub organization sources"
fi

if ! need_live; then
  skip "live source checks disabled; run with --live to verify source URLs"
  exit 0
fi

urls=(
  "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"
  "https://www.wired.com/feed/tag/ai/latest/rss"
  "https://www.technologyreview.com/feed/"
  "https://techcrunch.com/category/artificial-intelligence/feed/"
  "https://tensorfeed.ai/api/news"
  "https://www.dailydoseofai.tech/rss.xml"
  "https://planet-ai.net/rss.xml"
  "https://www.tmtpost.com/user/7944025"
  "https://maomu.com/news"
  "https://daily.xiaohu.ai/"
  "https://hex2077.dev/docs/"
)

for url in "${urls[@]}"; do
  info "checking $url"
  ok=0
  for attempt in 1 2; do
    if curl -L --compressed --fail --silent --show-error --max-time 40 --connect-timeout 10 -A "Mozilla/5.0" -o /dev/null "$url"; then
      ok=1
      break
    fi
    info "retrying $url"
  done
  if [[ "$ok" == 1 ]]; then
    pass "$url is reachable"
  else
    fail "$url is not reachable"
  fi
done
