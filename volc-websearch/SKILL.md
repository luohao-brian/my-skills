---
name: volc-websearch
description: 使用 Tavily、Bocha、火山引擎融合搜索做联网检索，并用 embedding 做结果去重和召回重排。当用户需要查询最新资讯、搜索新闻、查官网资料、限定站点搜索或需要有来源支撑的回答时使用。
homepage: https://www.volcengine.com/docs/85508/1650263
metadata: {"openclaw":{"requires":{"env":["TAVILY_API_KEY","BOCHA_API_KEY","VE_ACCESS_KEY","VE_SECRET_KEY","SEARCH_EMBEDDING_PROVIDER","SEARCH_EMBEDDING_MODEL","SEARCH_EMBEDDING_BASE_URL","SEARCH_EMBEDDING_API_KEY"]},"emoji":"🔍"}}
---

# 融合联网搜索

同时调用 Tavily、Bocha、火山引擎融合信息搜索 API 执行联网搜索，并用 embedding 做近重复去重和相关性重排，返回适合 AI 处理的网页结果。

## 何时使用

- 需要联网搜索，而不是依赖模型记忆
- 需要确认"今天 / 最近 / 最新 / 当前"的信息
- 需要搜索新闻、公告、政策、价格、活动、产品动态
- 需要从特定站点或官网获取信息
- 需要给回答附上来源链接

## 必需环境变量

- `TAVILY_API_KEY`：Tavily 搜索 API Key
- `BOCHA_API_KEY`：Bocha 搜索 API Key
- `VE_ACCESS_KEY`：火山引擎 Access Key ID
- `VE_SECRET_KEY`：火山引擎 Secret Access Key
- `SEARCH_EMBEDDING_PROVIDER`：embedding 提供方，当前固定使用 `openai`
- `SEARCH_EMBEDDING_MODEL`：embedding 模型名，例如 `doubao-embedding-large-text-240915`
- `SEARCH_EMBEDDING_BASE_URL`：embedding API Base URL，例如 `https://ark.cn-beijing.volces.com/api/v3`
- `SEARCH_EMBEDDING_API_KEY`：embedding API Key

这 8 个变量缺一不可。技能不会降级到单一搜索源，也不会在缺少 embedding 配置时继续运行。

## 基本搜索

```bash
{baseDir}/bin/volc-websearch "搜索词"
{baseDir}/bin/volc-websearch "搜索词" --count 15
```

## 常用参数

- `--count <n>`：最终返回条数，默认 15，最多 50 条
- `--type <type>`：当前仅支持 `web`
- `--time-range <range>`：时间范围，可选 `OneDay`、`OneWeek`、`OneMonth`、`OneYear`，或日期区间 `2024-12-30..2025-12-30`
- `--sites <a|b>`：限定站点搜索，多个站点用 `|` 分隔
- `--block-hosts <a|b>`：排除站点，多个站点用 `|` 分隔
- `--auth-level 1`：优先权威来源，主要作用于火山源，同时参与融合重排

## 模式选择

- 用 `web`：普通事实查询、网页检索、查官网内容
- 加 `--time-range`：用户关心最近动态、新闻、时效性内容
- 加 `--sites`：用户指定官网、官方媒体、文档站或垂直站点
- 加 `--auth-level 1`：医疗、政策、金融、科研等更看重可信度的主题

## 推荐用法示例

```bash
# 查最近新闻
{baseDir}/bin/volc-websearch "OpenAI 最新发布" --time-range OneWeek

# 查官网资料
{baseDir}/bin/volc-websearch "Responses API 文档" --sites "platform.openai.com|openai.com"

# 查权威来源
{baseDir}/bin/volc-websearch "流感疫苗安全性" --auth-level 1
```

## 回答规则

- 基于搜索结果作答，不要编造搜索结果中没有支持的信息
- 优先保留标题、站点名、URL
- 涉及时效性问题时，优先使用时间过滤并明确说明时间范围
- 融合阶段已经做了跨源去重和重排，但仍应人工判断结果是否互相印证
- 涉及高可信度主题时，优先使用限定站点或权威来源过滤
- 如果搜索结果不足以支持明确结论，应直接说明证据不足

## 故障排查

- 缺少凭证：检查 3 个搜索源和 embedding 的环境变量是否全部存在
- 需要查 API 参数、字段、错误码：打开 [references/docs-index.md](references/docs-index.md)
- 如果返回权限错误，优先检查服务是否已开通、凭证是否有效、子账号是否已授权
- 如果某个第三方搜索源返回结构变化，需要同步更新 Rust 侧 provider 解析逻辑

## 参考资料

按需打开以下文件，不必默认全部加载：

- [references/setup-guide.md](references/setup-guide.md)：服务开通、凭证申请、环境变量配置
- [references/docs-index.md](references/docs-index.md)：API 文档索引、参数说明、错误码速查
