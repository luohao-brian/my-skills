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

这里不只看“能不能打开”，更看“是不是高信号入口”。

| 品牌 | 更合适的优先入口 | 访问说明 | 质量判断 |
| --- | --- | --- | --- |
| OpenAI | `https://help.openai.com/en/articles/9624314-model-release-notes` `https://help.openai.com/en/articles/6825453-chatgpt-release-notes` `https://platform.openai.com/docs/changelog` `https://openai.com/index/` | Help Center 和平台 changelog 更贴近模型 / 产品 / API 更新；简单 HTTP 可能遇到 Cloudflare，优先浏览器抓取或搜索结果回源 | 高，适合核心产品、新模型、新功能、API 变化 |
| Anthropic | `https://www.anthropic.com/news` `https://docs.anthropic.com/en/release-notes/api` | `news` 适合重大公告，API release notes 适合开发者更新 | 高，覆盖模型、API、系统卡、安全能力 |
| Google AI / DeepMind | `https://blog.google/innovation-and-ai/technology/ai/` `https://blog.google/products/gemini/` `https://deepmind.google/blog/` | Google Blog 适合 Gemini 产品更新，DeepMind Blog 适合研究 / 模型发布 | 高，产品与研究分层清晰 |
| xAI | `https://x.ai/blog` `https://x.ai/news/grok` `https://x.ai/contact/` | `x.ai/blog` 比 `x.ai/news` 更像稳定入口；若直抓失败，转官方域名搜索与官方 X 账号检索 | 中高，内容一手但访问稳定性一般 |
| MiniMax | `https://www.minimaxi.com/news` | 直接新闻页可用；官网首页可作为备选 | 中高，适合产品和品牌动态 |
| 智谱 AI | `https://www.zhipuai.cn/zh/news` `https://www.zhipuai.cn/zh/research` | `news` 适合公告与产品动态，`research` 适合技术 / 模型发布 | 中高，中文一手信息较完整 |
| Kimi / Moonshot | `https://platform.moonshot.cn/blog` | 不要优先用 `moonshot.cn/blog`；`platform.moonshot.cn/blog` 才是稳定的官方更新页 | 高，产品发布和 API 更新信号强 |
| 阿里 AI / Qwen | `https://qwenlm.github.io/zh/blog/` `https://github.com/QwenLM/Qwen/releases` `https://qwen.ai/` | 不要优先用 `tongyi.aliyun.com` landing page；Qwen 官方博客和 GitHub Releases 更有价值 | 高，尤其适合开源模型、技术发布、版本更新 |
| 腾讯 AI / 混元 | `https://cloud.tencent.com/document/product/1729/104753` `https://hunyuan.tencent.com/` | `产品概述` 这种带更新时间的官方文档比纯 landing page 更有用；官网用于品牌锚点 | 中，技术参数强，新闻性一般 |
| 火山引擎 / 豆包 / 方舟 | `https://developer.volcengine.com/articles/7533460184351146010` `https://developer.volcengine.com/articles/7572608312823906331` `https://www.volcengine.com/product/ark` | 优先开发者社区的官方发布文章；纯产品页更多是介绍，不适合追更新 | 中，发布会和产品更新有价值，但入口分散 |
| Manus | `https://manus.im/de/blog` `https://manus.im/es/blog` `https://manus.im/it/blog` | 有官方 blog，但内容混杂产品更新与 SEO / listicle；只抽取 `产品` 类条目 | 中低，需严格筛噪音 |

补充规则：

- 官方社媒默认只做补充，不作为首选引用。
- 搜官方社媒时，不要先打开时间线，优先搜索“品牌名 + official + 产品名”。
- 对 OpenAI、xAI 这类站点，若官方页面抓取失败，立刻转为官方域名定向搜索，而不是直接降级成媒体报道。
- `openai.com/news/`、`help.openai.com`、`platform.openai.com/docs/changelog` 在简单 HTTP 或无状态请求下可能遇到 Cloudflare challenge；不应剔除，但访问方式必须改成“浏览器抓取或搜索回源”。
- `x.ai/news` 当前简单 HTTP 常见 Cloudflare challenge，建议优先使用 `x.ai/blog` 和官方 X 账号搜索。
- `www.moonshot.cn/blog` 当前更像通用壳页面，不是稳定新闻索引，已经降级；Moonshot 直接用 `platform.moonshot.cn/blog`。
- `tongyi.aliyun.com` 更像产品说明 landing page，新闻价值偏低；阿里相关更新优先看 Qwen 官方博客和 GitHub Releases。
- `qwenlm.ai/` 会跳到产品页 `chat.qwen.ai/`，品牌价值高，但新闻价值低；适合作为搜索锚点，不适合作为直抓入口。
- `www.minimaxi.com/news`、`www.zhipuai.cn/zh/news` 当前可用，不建议剔除。
- `ai.hubtoday.app/`、`maomu.com/news` 可保留，但只能放在低权重补漏层。

## 信息源价值排序

默认按下面的优先顺序和权重理解来源价值：

1. `S` 级，权重最高
   - 官方 release notes、官方 changelog、官方技术 / 产品博客、官方新闻页
   - 这层应占最终成稿的主体
   - 代表：OpenAI Help release notes / changelog、Anthropic API release notes、Google Gemini / DeepMind Blog、Moonshot Blog、Qwen Blog / GitHub Releases
2. `A` 级
   - 官方文档页、官方产品说明页、官方 X / Twitter
   - 适合补小版本更新、灰度功能、开发者接口变化
   - 代表：腾讯混元产品概述、火山引擎官方文章、xAI 官方 X、OpenAI / Anthropic 官方 X
3. `B` 级
   - 权威媒体与专业科技媒体
   - 用于补融资、采访、合作、行业影响，也用于交叉验证
   - 代表：The Verge、Wired、TechCrunch、MIT Technology Review
4. `C` 级
   - 主题聚合站和 curated feed
   - 用于发现热点，不直接当一手来源
   - 代表：HubToday AI
5. `D` 级
   - 泛聚合站、社区帖子、Reddit、论坛
   - 只用于发现线索、验证用户反馈、排查争议，不直接当主来源
   - 代表：猫目 Maomu、Reddit 讨论串

## 低权重源的处理建议

- `HubToday AI`
  - 保留，但放在 `C` 级补漏层
  - 用于发现当天热点和漏报
  - 一旦发现候选，尽量追到原始来源链接
- `猫目 Maomu`
  - 保留，但放在 `D` 级补漏层
  - 更适合做中文侧热点感知，不适合作为正式引用
  - 如果同一条新闻已经有官方源或权威媒体源，默认忽略 Maomu
- `Reddit`
  - 只用于用户反馈、服务故障、订阅问题、争议事件的旁证
  - 不用于正常产品发布的主成稿

## 媒体与聚合补充源矩阵

这些源只用于补漏和发现热点，成稿时尽量回到原始来源。

| 来源 | URL | 作用 |
| --- | --- | --- |
| The Verge AI | `https://www.theverge.com/ai-artificial-intelligence` | `B` 级，国际产品发布、行业动态 |
| Wired AI RSS | `https://www.wired.com/feed/tag/ai/latest/rss` | `B` 级，深度稿、趋势与治理 |
| TechCrunch RSS | `https://techcrunch.com/feed/` | `B` 级，融资、创业、产品更新 |
| 猫目 Maomu | `https://maomu.com/news` | `D` 级，中文热点、快讯补漏 |
| HubToday AI | `https://ai.hubtoday.app/` | `C` 级，当天热点、聚合发现 |
| MIT Technology Review RSS | `https://www.technologyreview.com/feed/` | `B` 级，深度报道、安全 / 治理 |

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
