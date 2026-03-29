# 新闻源与补充检索策略

这份文档只保留高信号规则。目标不是列一堆站点，而是明确：

1. 先扫哪些官方源
2. 哪些媒体源用于补漏
3. `tavily`、`bocha`、`brave` 分别负责什么

## 使用原则

1. 先固定源，后搜索补漏。
2. 官方源优先于媒体源，媒体源优先于泛搜索结果。
3. RSS 优先于网页列表页；列表页字段不完整时再抓详情页。
4. 对 OpenAI、xAI 这类可能有反爬挑战的官方站点，不要因为简单 HTTP 失败就视为无效。
5. 定向搜索时优先搜官方域名、官方品牌名、官方产品名。

## 官方一级优先源矩阵

先扫下面这些官方页面和官方品牌，再做搜索补漏。

| 品牌 | 官方页面优先入口 | 官方搜索锚点 | 重点主题 |
| --- | --- | --- | --- |
| OpenAI | `https://openai.com/news/` `https://openai.com/index/` | `openai.com`, `OpenAI`, `ChatGPT` | 模型、API、Agents、语音、多模态、开发者功能 |
| Anthropic | `https://www.anthropic.com/news` | `anthropic.com`, `Anthropic`, `Claude` | 模型、安全、企业能力、工具使用 |
| Google AI / DeepMind | `https://blog.google/innovation-and-ai/technology/ai/` `https://deepmind.google/blog/` | `blog.google`, `deepmind.google`, `Gemini`, `DeepMind` | 模型研究、产品功能、开发者工具 |
| xAI | `https://x.ai/news` `https://x.ai/` | `x.ai`, `xAI`, `Grok` | 新模型、新能力、X 平台集成 |
| MiniMax | `https://www.minimaxi.com/` `https://www.minimaxi.com/news` | `minimaxi.com`, `MiniMax` | 模型、语音、视频、Agent |
| 智谱 AI | `https://www.zhipuai.cn/` `https://www.zhipuai.cn/news` | `zhipuai.cn`, `智谱`, `GLM` | GLM、Agent、企业产品、开源 |
| Kimi / Moonshot | `https://www.moonshot.cn/` `https://www.moonshot.cn/blog` | `moonshot.cn`, `Kimi`, `Moonshot` | 长上下文、搜索、Agent、产品更新 |
| 阿里 AI | `https://qwenlm.ai/` `https://tongyi.aliyun.com/` | `qwenlm.ai`, `tongyi.aliyun.com`, `Qwen`, `通义` | 开源模型、企业能力、推理、多模态 |
| 腾讯 AI | `https://hunyuan.tencent.com/` `https://cloud.tencent.com/product/hunyuan` | `hunyuan.tencent.com`, `混元`, `腾讯 AI` | 混元模型、企业 API、生态合作 |
| 火山引擎 | `https://www.volcengine.com/` `https://www.volcengine.com/product/ark` | `volcengine.com`, `火山引擎`, `方舟`, `豆包` | 企业 AI 平台、模型、语音 / 视频 |
| Manus | `https://www.manus.im/` `https://www.manus.im/blog` | `manus.im`, `Manus` | Agent 工作流、产品更新、发布公告 |

补充规则：

- 官方社媒默认只做补充，不作为首选引用。
- 搜官方社媒时，不要先打开时间线，优先搜索“品牌名 + official + 产品名”。
- 对 OpenAI、xAI 这类站点，若官方页面抓取失败，立刻转为官方域名定向搜索，而不是直接降级成媒体报道。

## 媒体与聚合补充源矩阵

这些源只用于补漏和发现热点，成稿时尽量回到原始来源。

| 来源 | URL | 作用 |
| --- | --- | --- |
| The Verge AI | `https://www.theverge.com/ai-artificial-intelligence` | 国际产品发布、行业动态 |
| Wired AI RSS | `https://www.wired.com/feed/tag/ai/latest/rss` | 深度稿、趋势与治理 |
| TechCrunch RSS | `https://techcrunch.com/feed/` | 融资、创业、产品更新 |
| 猫目 Maomu | `https://maomu.com/news` | 中文热点、快讯补漏 |
| HubToday AI | `https://ai.hubtoday.app/` | 当天热点、聚合发现 |
| MIT Technology Review RSS | `https://www.technologyreview.com/feed/` | 深度报道、安全 / 治理 |

## 搜索引擎分工

### Tavily

优先用于：

- 宽召回
- 时效新闻
- 深度补漏
- 官方域名定向搜索

典型 query：

- `OpenAI GPT-5.4 2026-03-29`
- `site:openai.com ChatGPT agents`
- `AI agent launch 2026-03-29`

### Bocha

优先用于：

- 中文宽度补充
- 中文站点补漏
- 中文热点发现

典型 query：

- `2026年3月29日 大模型 发布`
- `2026年3月29日 Agent 上线`
- `智谱 AI GLM 发布`

### Brave

优先用于：

- 英文国际动态
- 英文交叉验证
- 官方品牌 / 官方社媒补充

典型 query：

- `OpenAI official GPT-5.4`
- `Anthropic Claude release 2026-03-29`
- `xAI Grok official update`

## 最低搜索覆盖要求

1. 至少使用 `tavily` 和 `bocha`。
2. 国际或英文动态补 `brave`。
3. 每个重要分类至少做一轮中文 query 和一轮英文 query。
4. 对重点公司至少做一轮官方域名定向检索。

## 推荐执行顺序

1. 扫官方一级优先源矩阵
2. 扫媒体与聚合补充源矩阵
3. 用 `tavily` 做宽召回和官方域名定向搜索
4. 用 `bocha` 补中文宽度
5. 用 `brave` 补英文宽度和英文交叉验证
6. 对命中条目抓详情页并补齐字段
