---
name: volc-websearch
description: 使用 Tavily、Bocha、Brave、火山引擎执行网页搜索，支持自动选择最优搜索引擎。当用户需要查询最新资讯、搜索新闻、查官网资料、限定站点搜索或需要有来源支撑的回答时使用。
homepage: https://www.volcengine.com/docs/85508/1650263
metadata: {"openclaw":{"requires":{"env":["TAVILY_API_KEY","BOCHA_API_KEY","BRAVE_API_KEY","VE_ACCESS_KEY","VE_SECRET_KEY"]},"emoji":"🔍"}}
---

# 智能网页搜索

执行来自指定搜索引擎的网页搜索，支持自动选择最优搜索引擎或手动选择特定引擎。

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

## 代理支持

websearch技能支持通过以下参数显式设置代理：

- `--http-proxy <url>`：HTTP代理URL，会覆盖环境变量HTTP_PROXY
- `--https-proxy <url>`：HTTPS代理URL，会覆盖环境变量HTTPS_PROXY
- `--no-proxy <hosts>`：配置了此参数但当前实现中会对所有请求使用代理

代理配置优先级：命令行参数 > 环境变量 > 无代理

注意：当前使用的HTTP客户端对no_proxy的支持有限，代理会对所有请求生效。

## 基本搜索

```bash
{baseDir}/bin/volc-websearch "搜索词"
{baseDir}/bin/volc-websearch "搜索词" --count 15
```

## 常用参数

- `--count <n>`：返回条数，默认 15，最多 50 条
- `--type <type>`：当前仅支持 `web`
- `--time-range <range>`：时间范围，可选 `OneDay`、`OneWeek`、`OneMonth`、`OneYear`，或日期区间 `2024-12-30..2025-12-30`
- `--sites <a|b>`：限定站点搜索，多个站点用 `|` 分隔
- `--block-hosts <a|b>`：排除站点，多个站点用 `|` 分隔
- `--auth-level 1`：优先权威来源，主要作用于火山源，同时参与融合重排
- `--http-proxy <url>`：HTTP代理URL，会覆盖环境变量HTTP_PROXY
- `--https-proxy <url>`：HTTPS代理URL，会覆盖环境变量HTTPS_PROXY
- `--no-proxy <hosts>`：不使用代理的主机列表，多个主机用逗号分隔，会覆盖环境变量NO_PROXY

## 模式选择

- 自动选择引擎：`--engine auto`（默认，智能选择最优搜索引擎）
- 选择特定引擎：`--engine tavily`、`--engine bocha`、`--engine brave`、`--engine volc`
- 用 `web`：普通事实查询、网页检索、查官网内容
- 加 `--time-range`：用户关心最近动态、新闻、时效性内容
- 加 `--sites`：用户指定官网、官方媒体、文档站或垂直站点
- 加 `--auth-level 1`：医疗、政策、金融、科研等更看重可信度的主题

### 自动选择逻辑

auto 模式会根据以下因素自动选择最合适的搜索引擎：

- 中文内容：优先选择 Bocha
- 新闻查询：优先选择 Tavily
- 技术文档：优先选择 Brave
- 一般查询：默认选择 Tavily

## 推荐用法示例

```bash
# 自动选择搜索引擎（推荐）
{baseDir}/bin/volc-websearch "Claude AI 最新发布"

# 强制使用 Tavily
{baseDir}/bin/volc-websearch "Claude AI" --engine tavily

# 强制使用 Brave（适合技术文档）
{baseDir}/bin/volc-websearch "Claude AI API documentation" --engine brave

# 强制使用 Bocha（适合中文内容）
{baseDir}/bin/volc-websearch "Claude AI 中文介绍" --engine bocha

# 强制使用火山引擎
{baseDir}/bin/volc-websearch "Claude AI" --engine volc

# 查最近新闻
{baseDir}/bin/volc-websearch "OpenAI 最新发布" --time-range OneWeek

# 查官网资料
{baseDir}/bin/volc-websearch "Responses API 文档" --sites "platform.openai.com|openai.com"

# 查权威来源
{baseDir}/bin/volc-websearch "流感疫苗安全性" --auth-level 1

# 使用代理（会覆盖环境变量）
{baseDir}/bin/volc-websearch "AI 趋势" --http-proxy http://proxy.company.com:8080 --https-proxy http://proxy.company.com:8080 --no-proxy "localhost,127.0.0.1,.internal"
```

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
- 如果某个第三方搜索源返回结构变化，需要同步更新 Rust 侧 provider 解析逻辑
- 代理配置：如果某个搜索源无法访问，尝试配置代理参数
- 使用特定引擎时只返回该引擎的结果，不会进行融合或去重

## 代理支持

websearch技能支持通过以下参数显式设置代理：

- `--http-proxy <url>`：HTTP代理URL，会覆盖环境变量HTTP_PROXY
- `--https-proxy <url>`：HTTPS代理URL，会覆盖环境变量HTTPS_PROXY
- `--no-proxy <hosts>`：配置了此参数但当前实现中会对所有请求使用代理

代理配置优先级：命令行参数 > 环境变量 > 无代理

注意：当前使用的HTTP客户端对no_proxy的支持有限，代理会对所有请求生效。当某个搜索源无法访问时，可以通过代理参数来解决问题。

## 参考资料

按需打开以下文件，不必默认全部加载：

- [references/setup-guide.md](references/setup-guide.md)：服务开通、凭证申请、环境变量配置
- [references/docs-index.md](references/docs-index.md)：API 文档索引、参数说明、错误码速查
