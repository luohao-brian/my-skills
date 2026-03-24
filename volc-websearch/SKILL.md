---
name: volc-websearch
description: 使用 Tavily、Bocha、Brave、火山引擎执行网页搜索，支持“query 只写主题、其他约束结构化表达”的统一参数层与多引擎交叉检索。当用户需要查询最新资讯、搜索新闻、查官网资料、限定站点搜索或需要有来源支撑的回答时使用。
homepage: https://www.volcengine.com/docs/85508/1650263
metadata: {"openclaw":{"requires":{"env":["TAVILY_API_KEY","BOCHA_API_KEY","BRAVE_API_KEY","VE_ACCESS_KEY","VE_SECRET_KEY"]},"emoji":"🔍"}}
---

# 智能网页搜索

执行来自 Tavily、Bocha、Brave、火山引擎的网页搜索。默认采用显式多引擎交叉检索，CLI 需要显式指定 `--engine`。

## 何时使用

- 需要联网搜索，而不是依赖模型记忆
- 需要确认"今天 / 最近 / 最新 / 当前"的信息
- 需要搜索新闻、公告、政策、价格、活动、产品动态
- 需要从特定站点或官网获取信息
- 需要给回答附上来源链接

## 必需环境变量

根据实际使用的搜索引擎，需要相应的 API Key：

- `TAVILY_API_KEY`：Tavily 搜索 API Key
- `BOCHA_API_KEY`：Bocha 搜索 API Key
- `BRAVE_API_KEY`：Brave 搜索 API Key
- `VE_ACCESS_KEY`：火山引擎 Access Key ID
- `VE_SECRET_KEY`：火山引擎 Secret Access Key

建议配置所有 API Key，以便不同 provider 能并行补充、互相校验。

## 核心原则

- `query` 只表达搜索主题本身，不要再把时间、地域、语言、站点限制塞进 `query`
- 时间、地域、语言、站点、意图、输出形态优先用结构化参数表达
- `--engine` 必须显式指定为 `bocha`、`brave`、`tavily`、`volc` 之一
- 如果强制指定某个 `--engine`，CLI 会只下推该 provider 原生支持的字段；不支持的字段会打印 warning，并被透明忽略，不会偷偷拼回 `query`
- 遇到“今天 / 最新 / 最近 / 今日新闻 / 日报 / 快讯”这类强时效问题，必须显式使用多个搜索引擎交叉验证，不能只跑单引擎结果
- 不同引擎要利用各自原生参数能力，不能把同一组参数机械地平移到所有 provider
- 当某个 provider 不支持关键结构化约束时，应补一轮“provider 原生参数 + 词面回退 query”的检索，而不是直接放弃该 provider

## 当前状态

- 这套结构化参数接口已经实装到 CLI 和 `SKILL.md`
- `tavily`、`brave`、`bocha`、`volc` 都做过真实联网验证
- provider 原生能力并不完全一致，所以 skill 采用的是“统一参数层 + 原生下推 + 透明降级”
- 当前 CLI 需要手动组合多引擎，时效类任务不能依赖单次单引擎检索

## 强时效新闻工作流

当用户要查“今天 / 今日 / 最新 / 最近 / 24 小时内 / 本周 AI 新闻 / 日报 / 快讯”时，按下面流程执行，不要偷懒成单次单引擎搜索：

1. 先明确日期窗口、语言、地域、站点、意图，不要边搜边猜。
2. 至少并行补三类 provider：
   - 一个“时效召回强”的引擎：优先 `tavily`
   - 一个“中文网页 / 日期补充验证”的引擎：优先 `volc`
   - 一个“中文召回 / 补漏”的引擎：优先 `bocha`
   - 需要跨语种或国家参数时，再额外加 `brave`
3. 对每个 provider 使用它擅长的参数，不要只复制同一套命令。
4. 对不支持时间下推的 provider，再补一轮词面日期 query。
5. 汇总时按“时间是否满足、来源是否可靠、是否与其他引擎互相印证”做去重。
6. 只把真正命中目标日期窗口的内容归入“今日动态”；其余结果要明确标成“历史结果”或直接剔除。

最低执行标准：

- 强时效问题至少跑 `3` 个 provider；跨语种或国际新闻建议 `4` 个
- 不能只给出单引擎一次调用的结果
- 不能因为某个 provider 不支持时间下推，就默认它“没有结果”

## 多引擎执行模板

处理强时效新闻时，优先按下面的矩阵执行：

1. `tavily`
   - 主打：相对时间召回、新闻意图、站点白名单
2. `volc`
   - 主打：中文站点、日期区间、权威站点补充验证
3. `bocha`
   - 主打：中文召回
   - 必须补一轮词面日期 query
4. `brave`
   - 只在以下情况强制加入：
   - 需要 `country/language`
   - 需要英文媒体或国际新闻补充
   - 需要校验中文结果是否被英文主流媒体印证

## Provider 参数使用策略

针对不同 provider，优先这样利用参数：

- `tavily`
  - 适合：新闻、最新动态、最近 24 小时、限定站点
  - 优先用：`--freshness`、`--intent news`、`--domain-filter`
  - 规避：查“今天 / 今日 / 当天”时，不要把同一天同时传给 `--date-after` 和 `--date-before`
  - 规避：不要把 `--freshness` 和 `--date-after/--date-before` 混用
- `volc`
  - 适合：中文网页、站点限制、日期窗口补充验证
  - 优先用：`--date-after` + `--date-before` 成对使用、`--domain-filter`
- `brave`
  - 适合：英文或跨语种补充、`country/language` 约束明显时
  - 优先用：`--country`、`--language`
  - 注意：当前时间约束不原生下推，日期要求强时不能只靠 Brave
- `bocha`
  - 适合：中文召回、补充中文站点结果、摸中文舆情面
  - 优先用：中文主题 + 合理 `--count`
  - 注意：当前时间范围不原生下推，必须结合词面日期 query 做补充轮次

## Query 回退例外

默认规则仍然是“不要把时间、站点、语言限制塞回 query”。

但在以下情况允许例外：

- provider 明确不支持目标约束的原生下推
- 该约束对任务又是硬条件，尤其是“今天新闻 / 指定日期新闻”

此时应先保留一轮结构化参数检索，再补一轮词面回退 query，例如：

- `2026-03-25 AI 新闻`
- `2026年3月25日 AI`
- `today AI news`

注意：

- 这种词面日期 query 只作为补充轮次，不替代 provider 的原生参数能力
- 汇总时必须标注这是“词面日期召回”，可信度低于原生时间过滤命中

## Tavily 日期规避规则

- 查“今天 / 今日 / 当天新闻”时，`tavily` 默认只用 `--freshness pd`
- 不要使用：
  - `--date-after 2026-03-25 --date-before 2026-03-25`
  - `--freshness pd --date-after 2026-03-25 --date-before 2026-03-25`
- 如果需要“自然日”硬过滤，让 `volc` 承担日期窗口，`tavily` 只负责最近 24 小时召回
- `--freshness` 只接受 `pd|pw|pm|py`，不要写成 `day|week|month|year`

## 基本搜索

```bash
{baseDir}/bin/volc-websearch "社会新闻" --engine bocha
{baseDir}/bin/volc-websearch "AI agent progress" --engine tavily --count 8
```

## 参数列表

- `query`：搜索主题本身，例如 `社会新闻`、`AI agent progress`
- `--engine <bocha|brave|tavily|volc>`：指定搜索引擎，必填
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
| `intent` | 部分映射到 `topic` | 仅作结果倾向提示 | 仅作结果倾向提示 | 部分映射到权威性偏好 |
| `result_type` | 本地输出整形 | 本地输出整形 | 本地输出整形 | 本地输出整形 |

说明：

- `result_type=summary` 当前是 skill 侧的输出形态控制，不是要求每个 provider 都切到自己的原生“总结接口”
- `country/language/date/domain` 这类结构化字段，只有 provider 有可靠原生字段时才会下推
- 不支持的字段不会被拼回 `query` 伪装成“支持”

## 手动选源逻辑

建议的手动选源顺序：

- 有显式日期窗口：让 `volc` 承担自然日硬过滤，`tavily` 负责相对时效召回
- 中文新闻：必须补 `bocha`
- 有 `country/language`：补 `brave`
- 有站点白名单：`tavily` 与 `volc` 都要跑
- 需要“今天新闻”结论时，不接受只靠一个 provider 的单边结果

## 推荐用法示例

```bash
# 搜索 2026-03-24 的中文社会新闻：至少显式跑 tavily + volc + bocha
{baseDir}/bin/volc-websearch "社会新闻" \
  --engine tavily \
  --freshness pd \
  --country CN \
  --intent news \
  --result-type list \
  --count 8

{baseDir}/bin/volc-websearch "社会新闻" \
  --engine volc \
  --date-after 2026-03-24 \
  --date-before 2026-03-24 \
  --domain-filter xinhuanet.com,people.com.cn,thepaper.cn \
  --intent news \
  --result-type list \
  --count 8

{baseDir}/bin/volc-websearch "2026年3月24日 社会新闻" \
  --engine bocha \
  --language zh \
  --result-type list \
  --count 8

# 搜索最近一周的 AI 进展：至少显式跑 tavily + bocha，必要时补 brave
{baseDir}/bin/volc-websearch "AI agent progress" \
  --engine tavily \
  --freshness pw \
  --intent news \
  --count 8

{baseDir}/bin/volc-websearch "AI agent progress" \
  --engine bocha \
  --count 8

# 限定官网域名查资料，并输出摘要形态
{baseDir}/bin/volc-websearch "Responses API" \
  --engine tavily \
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

{baseDir}/bin/volc-websearch "AI 新闻" \
  --engine tavily \
  --freshness pd \
  --country CN \
  --intent news \
  --count 10

{baseDir}/bin/volc-websearch "2026年3月25日 AI 新闻" \
  --engine bocha \
  --language zh \
  --count 10

{baseDir}/bin/volc-websearch "AI 新闻" \
  --engine volc \
  --date-after 2026-03-25 \
  --date-before 2026-03-25 \
  --domain-filter xinhuanet.com,people.com.cn,thepaper.cn \
  --intent news \
  --count 10

# 使用代理
{baseDir}/bin/volc-websearch "AI 趋势" \
  --engine tavily \
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
- 如果任务是“今天 / 最新 / 日报”，回答中应明确写出：
  - 实际使用了哪些 provider
  - 哪些结果来自原生时间过滤
  - 哪些结果只是词面日期召回
  - 哪些旧闻被排除

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
