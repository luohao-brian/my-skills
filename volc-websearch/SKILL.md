---
name: volc-websearch
description: 使用 Tavily、Bocha、Brave、火山引擎执行网页搜索，支持“query 只写主题、其他约束结构化表达”的统一参数层和自动选源。当用户需要查询最新资讯、搜索新闻、查官网资料、限定站点搜索或需要有来源支撑的回答时使用。
homepage: https://www.volcengine.com/docs/85508/1650263
metadata: {"openclaw":{"requires":{"env":["TAVILY_API_KEY","BOCHA_API_KEY","BRAVE_API_KEY","VE_ACCESS_KEY","VE_SECRET_KEY"]},"emoji":"🔍"}}
---

# 智能网页搜索

执行来自 Tavily、Bocha、Brave、火山引擎的网页搜索，支持自动选择最合适的搜索引擎，也支持手动固定某个 provider。

## 何时使用

- 需要联网搜索，而不是依赖模型记忆
- 需要确认"今天 / 最近 / 最新 / 当前"的信息
- 需要搜索新闻、公告、政策、价格、活动、产品动态
- 需要从特定站点或官网获取信息
- 需要给回答附上来源链接

## 必需环境变量

根据实际使用的搜索引擎，需要相应的 API Key：

- `TAVILY_API_KEY`：Tavily 搜索 API Key（使用 --engine tavily 或 --engine auto 时可能需要）
- `BOCHA_API_KEY`：Bocha 搜索 API Key（使用 --engine bocha 或 --engine auto 时可能需要）
- `BRAVE_API_KEY`：Brave 搜索 API Key（使用 --engine brave 或 --engine auto 时可能需要）
- `VE_ACCESS_KEY`：火山引擎 Access Key ID（使用 --engine volc 或 --engine auto 时可能需要）
- `VE_SECRET_KEY`：火山引擎 Secret Access Key（使用 --engine volc 或 --engine auto 时可能需要）

建议配置所有 API Key，以便 auto 模式能够正常工作。

## 核心原则

- `query` 只表达搜索主题本身，不要再把时间、地域、语言、站点限制塞进 `query`
- 时间、地域、语言、站点、意图、输出形态优先用结构化参数表达
- `--engine auto` 会优先选择最能原生支持这些结构化约束的 provider
- 如果强制指定某个 `--engine`，CLI 会只下推该 provider 原生支持的字段；不支持的字段会打印 warning，并被透明忽略，不会偷偷拼回 `query`

## 当前状态

- 这套结构化参数接口已经实装到 CLI 和 `SKILL.md`
- `tavily`、`brave`、`bocha`、`volc` 都做过真实联网验证
- `auto` 模式也做过真实回归，能在 provider 失败时自动回退
- provider 原生能力并不完全一致，所以 skill 采用的是“统一参数层 + 原生下推 + 透明降级”

## 基本搜索

```bash
{baseDir}/bin/volc-websearch "社会新闻"
{baseDir}/bin/volc-websearch "AI agent progress" --count 8
```

## 参数列表

- `query`：搜索主题本身，例如 `社会新闻`、`AI agent progress`
- `--engine <auto|bocha|brave|tavily|volc>`：指定搜索引擎，默认 `auto`
- `--count <n>`：返回结果数量，默认 15，最多 50
- `--freshness <pd|pw|pm|py>`：快捷时间范围，分别表示 1 天、1 周、1 月、1 年
- `--date-after <YYYY-MM-DD>`：起始日期
- `--date-before <YYYY-MM-DD>`：结束日期
- `--country <code>`：地域过滤提示，例如 `CN`、`US`
- `--language <code>`：语言过滤提示，例如 `zh`、`en`
- `--domain-filter <a,b>`：域名白名单，可用逗号分隔，也可重复传参
- `--intent <discover|news|fact|source_finding>`：搜索意图提示
- `--result-type <list|summary>`：返回列表或摘要形态
- `--http-proxy <url>`：HTTP 代理
- `--https-proxy <url>`：HTTPS 代理
- `--no-proxy <hosts>`：不走代理的主机列表

## Provider 支持矩阵

| 参数 | Tavily | Bocha | Brave | Volc |
|------|--------|-------|-------|------|
| `query` | 原生 | 原生 | 原生 | 原生 |
| `engine` | 调度层 | 调度层 | 调度层 | 调度层 |
| `count` | 原生 | 原生 | 原生 | 原生 |
| `freshness` | 原生 | 未下推 | 未下推 | 映射到 `TimeRange` |
| `date_after` / `date_before` | 原生 | 未下推 | 未下推 | 两端都提供时映射到 `TimeRange` |
| `country` | 原生（country boost） | 未下推 | 原生 | 未下推 |
| `language` | 当前未下推 | 未下推 | 原生（`search_lang`） | 未下推 |
| `domain_filter` | 原生（`include_domains`） | 未下推 | 未下推 | 映射到 `Sites` |
| `intent` | 部分映射到 `topic` | 主要用于 auto 选源 | 主要用于 auto 选源 | 部分映射到权威性偏好 |
| `result_type` | 本地输出整形 | 本地输出整形 | 本地输出整形 | 本地输出整形 |

说明：

- `result_type=summary` 当前是 skill 侧的输出形态控制，不是要求每个 provider 都切到自己的原生“总结接口”
- `country/language/date/domain` 这类结构化字段，只有 provider 有可靠原生字段时才会下推
- 不支持的字段不会被拼回 `query` 伪装成“支持”

## 自动选择逻辑

auto 模式会优先考虑结构化约束，然后再看 query 本身：

- 有 `country` 或 `language`：优先 Brave，其次 Tavily
- 有 `domain_filter`：优先 Tavily，其次 Volc
- 有 `freshness` 或显式日期：优先 Tavily，其次 Volc
- `intent=news`：优先 Tavily
- `intent=source_finding` 或 query 像技术文档：优先 Brave
- 中文主题：在没有更强结构化约束时优先 Bocha

## 推荐用法示例

```bash
# 搜索 2026-03-24 的中文社会新闻，推荐交给 auto 选最合适 provider
{baseDir}/bin/volc-websearch "社会新闻" \
  --date-after 2026-03-24 \
  --date-before 2026-03-24 \
  --country CN \
  --language zh \
  --intent news \
  --result-type list \
  --count 8

# 搜索最近一周的 AI 进展，自动选最合适 provider
{baseDir}/bin/volc-websearch "AI agent progress" --freshness pw --intent news --count 8

# 限定官网域名查资料，并输出摘要形态
{baseDir}/bin/volc-websearch "Responses API" \
  --domain-filter platform.openai.com,openai.com \
  --intent source_finding \
  --result-type summary

# 强制使用 Brave 查美国英文资料
{baseDir}/bin/volc-websearch "interest rates" \
  --engine brave \
  --country US \
  --language en \
  --intent fact

# 强制使用 Volc 做站点限制搜索
{baseDir}/bin/volc-websearch "Responses API" \
  --engine volc \
  --domain-filter platform.openai.com,openai.com \
  --intent source_finding \
  --result-type summary

# 强制使用 Bocha 做中文基础搜索
{baseDir}/bin/volc-websearch "社会新闻" --engine bocha --count 8

# 使用代理
{baseDir}/bin/volc-websearch "AI 趋势" \
  --http-proxy http://proxy.company.com:8080 \
  --https-proxy http://proxy.company.com:8080 \
  --no-proxy "localhost,127.0.0.1,.internal"
```

## 兼容参数

以下旧参数仍可用，但不再推荐写进新 prompt 或新文档：

- `--time-range <OneDay|OneWeek|OneMonth|OneYear|YYYY-MM-DD..YYYY-MM-DD>`
- `--sites <a|b>`
- `--block-hosts <a|b>`
- `--auth-level 1`

websearch技能支持通过以下参数显式设置代理：

- `--http-proxy <url>`：HTTP代理URL，会覆盖环境变量HTTP_PROXY
- `--https-proxy <url>`：HTTPS代理URL，会覆盖环境变量HTTPS_PROXY
- `--no-proxy <hosts>`：配置了此参数但当前实现中会对所有请求使用代理

代理配置优先级：命令行参数 > 环境变量 > 无代理

注意：当前使用的HTTP客户端对no_proxy的支持有限，代理会对所有请求生效。

## 回答规则

- 基于搜索结果作答，不要编造搜索结果中没有支持的信息
- 优先保留标题、站点名、URL
- 涉及时效性问题时，优先使用时间过滤并明确说明时间范围
- 由于返回的是原始搜索结果，可能存在重复，应人工判断结果是否互相印证
- 涉及高可信度主题时，优先使用限定站点或权威来源过滤
- 如果搜索结果不足以支持明确结论，应直接说明证据不足

## 故障排查

- 缺少凭证：检查实际使用的搜索引擎对应的环境变量是否已设置
- 需要查 API 参数、字段、错误码：打开 [references/docs-index.md](references/docs-index.md)
- 如果返回权限错误，优先检查服务是否已开通、凭证是否有效、子账号是否已授权
- 如果看起来“能搜到，但某些过滤条件没生效”，先对照上面的 provider 支持矩阵
- 如果某个第三方搜索源返回结构变化，需要同步更新 Rust 侧 provider 解析逻辑
- 如果强制指定 provider 且看到 warning，表示有部分结构化字段未被该 provider 原生支持
- 代理配置：如果某个搜索源无法访问，尝试配置代理参数
- 使用特定引擎时只返回该引擎的结果，不会进行融合或去重

## 参考资料

按需打开以下文件，不必默认全部加载：

- [references/setup-guide.md](references/setup-guide.md)：服务开通、凭证申请、环境变量配置
- [references/docs-index.md](references/docs-index.md)：API 文档索引、参数说明、错误码速查
