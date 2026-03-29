# 新闻源与补充检索策略

本文档定义 `ai-news` 的官方优先源、媒体补充源、验证状态、抓取优先级和分类补充策略。先扫官方源，再扫媒体与聚合源，最后做多搜索引擎补漏。

验证时间：2026-03-29

## 使用原则

1. 先固定源，后搜索补漏。
2. RSS 优先于网页列表页。
3. 列表页字段不完整时，再抓详情页。
4. 站点可访问但本机浏览器 fallback 失败，不等于站点失效。
5. 只删除真正失效、长期不可访问或明显不适合采集的源。

## 官方一级优先源

日报场景下，以下公司与产品线的官方渠道优先级高于媒体报道。只要官方源里已经有一手公告、产品更新或技术发布，成稿时应优先引用官方链接。

### OpenAI

- 官网 / 新闻页:
  - https://openai.com/news/
  - https://openai.com/index/
- 类型: 官方官网 / 新闻页
- 状态: 2026-03-29 简单 HTTP 会遇到 `403 Cloudflare challenge`
- 抓取策略:
  - 优先用 `url-to-markdown` / `web-fetch` 浏览器抓取
  - 如果直接抓失败，用 `volc-websearch` 对 `openai.com` 做定向搜索
  - 再补官方 X / 产品账号搜索
- 关注内容: ChatGPT、API、模型发布、推理能力、Agents、语音、多模态、开发者功能

### Anthropic

- 官网 / 新闻页:
  - https://www.anthropic.com/news
- 类型: 官方新闻页
- 状态: 2026-03-29 `HTTP 200`
- 抓取策略: 官方新闻页优先，再补官方 X 检索
- 关注内容: Claude、API、模型、安全、企业能力、工具使用

### Google AI / Google DeepMind

- 官网 / 博客:
  - https://blog.google/innovation-and-ai/technology/ai/
  - https://blog.google/innovation-and-ai/
  - https://deepmind.google/blog/
- 类型: 官方博客 / 官方研究博客
- 状态:
  - `blog.google` 2026-03-29 `HTTP 200`
  - `deepmind.google/discover/blog/` 会跳转到 `https://deepmind.google/blog/`
- 抓取策略: 官方博客优先，再补 Google AI / Google DeepMind 官方 X 检索
- 关注内容: Gemini、DeepMind、模型研究、产品功能、开发者工具、基础设施

### xAI

- 官网 / 新闻页:
  - https://x.ai/news
  - https://x.ai/
- 类型: 官方官网 / 新闻页
- 状态: 2026-03-29 简单 HTTP 会遇到 `403 Cloudflare challenge`
- 抓取策略:
  - 优先浏览器抓取
  - 如果失败，用 `volc-websearch` 定向搜 `site:x.ai`
  - 再补 xAI / Grok 官方 X 检索
- 关注内容: Grok、新模型、新能力、X 平台集成、开发者接口

### MiniMax

- 官网:
  - https://www.minimaxi.com/
  - https://www.minimaxi.com/news
- 类型: 官方官网 / 新闻页
- 状态:
  - 官网 2026-03-29 `HTTP 200`
  - `/news` 需要实时抓取确认
- 抓取策略: 官网与新闻页优先，再补官方社媒检索
- 关注内容: 模型、语音、视频、Agent、出海产品更新

### 智谱 AI

- 官网:
  - https://www.zhipuai.cn/
  - https://www.zhipuai.cn/news
- 类型: 官方官网 / 新闻页
- 状态:
  - 官网 2026-03-29 返回跳转
  - `/news` 需要浏览器或搜索回退确认
- 抓取策略: 官网 / 新闻页优先，再补官方社媒与中文搜索
- 关注内容: GLM、Agent、企业产品、开源、生态合作

### Kimi / Moonshot

- 官网:
  - https://www.moonshot.cn/
  - https://www.moonshot.cn/blog
- 类型: 官方官网 / 博客
- 状态:
  - 官网 2026-03-29 `HTTP 200`
  - `/blog` 需要实时抓取确认
- 抓取策略: 官网 / 博客优先，再补官方社媒与中文搜索
- 关注内容: Kimi、长上下文、搜索、Agent、产品更新

### 阿里 AI

- 官网 / 产品页:
  - https://qwenlm.ai/
  - https://tongyi.aliyun.com/
- 类型: 官方模型站 / 官方产品页
- 状态:
  - 需要实时抓取确认
  - `alibabacloud.com/blog` 当前不是稳定入口，不作为优先源
- 抓取策略:
  - 优先 Qwen / 通义官方站点
  - 再用 `volc-websearch` 定向检索 `qwenlm.ai`、`tongyi.aliyun.com`
  - 需要时再补阿里云相关官方博客
- 关注内容: Qwen、通义、开源模型、企业能力、推理和多模态

### 腾讯 AI

- 官网 / 产品页:
  - https://hunyuan.tencent.com/
  - https://cloud.tencent.com/product/hunyuan
  - https://www.tencent.com/zh-cn/business/ai.html
- 类型: 官方产品页 / 公司 AI 页面
- 状态:
  - `hunyuan.tencent.com` 2026-03-29 `HTTP 200`
  - 其他页面需要实时抓取确认
- 抓取策略: 混元产品页优先，再补腾讯云与腾讯官方社媒 / 公告
- 关注内容: 混元模型、企业 API、应用场景、生态合作

### 火山引擎

- 官网 / 产品页:
  - https://www.volcengine.com/
  - https://www.volcengine.com/product/ark
- 类型: 官方官网 / 产品页
- 状态:
  - 官网 2026-03-29 `HTTP 200`
  - `product/ark` 需要实时抓取确认
- 抓取策略: Ark / 火山引擎产品页优先，再补官方博客与发布会内容
- 关注内容: 方舟、豆包模型、企业 AI 平台、语音 / 视频 / 多模态能力

### Manus

- 官网 / 博客:
  - https://www.manus.im/
  - https://www.manus.im/blog
- 类型: 官方官网 / 博客
- 状态:
  - 官网 2026-03-29 `HTTP 200`
  - `/blog` 需要实时抓取确认
- 抓取策略: 官网 / 博客优先，再补官方 X 检索
- 关注内容: Manus 产品更新、Agent 能力、自动化工作流、发布公告

### 官方 X / Twitter 渠道

- 类型: 官方社媒渠道
- 状态: X 页面本身经常不适合直接全文抓取
- 抓取策略:
  - 不强依赖直接打开 X 时间线
  - 用 `volc-websearch` / `brave` 搜索“品牌名 + official X + 产品名”
  - 搜到官方帖子后，再结合官网或媒体二次验证
- 用途:
  - 补产品小版本更新
  - 补功能灰度上线
  - 补尚未进入官网新闻页的技术公告

## 媒体与聚合补充源

### The Verge AI

- URL: https://www.theverge.com/ai-artificial-intelligence
- 类型: 栏目页
- 状态: 2026-03-29 `HTTP 200`
- 适用分类: 大模型、Agent、应用 / 产品、安全 / 治理
- 用法: 先扫栏目页，再对命中的详情页做正文抓取
- 备注: 国际媒体覆盖广，适合发现产品发布和行业动态

### Wired AI RSS

- URL: https://www.wired.com/feed/tag/ai/latest/rss
- 类型: RSS
- 状态: 2026-03-29 `HTTP 200`
- 适用分类: 大模型、安全 / 治理、应用 / 产品
- 用法: 先读 RSS，再按需抓详情页
- 备注: 深度稿较多，适合补背景和趋势

### TechCrunch RSS

- URL: https://techcrunch.com/feed/
- 类型: RSS
- 状态: 2026-03-29 `HTTP 200`
- 适用分类: 融资 / 商业、应用 / 产品、开源
- 用法: 在 RSS 中筛 AI 关键词，再抓详情页确认
- 备注: 不是 AI 专属 feed，必须做主题过滤

### 猫目 Maomu

- URL: https://maomu.com/news
- 类型: 中文新闻聚合页
- 状态: 2026-03-29 `HTTP 200`
- 适用分类: 应用 / 产品、Agent、开源、中文快讯补漏
- 用法: 优先扫描列表页，对高价值条目再抓详情页
- 备注: 中文聚合站，适合补中文侧覆盖

### HubToday AI

- URL: https://ai.hubtoday.app/
- 类型: AI 资讯聚合页
- 状态: 2026-03-29 `HTTP 200`
- 适用分类: 大模型、Agent、应用 / 产品、开源
- 用法: 先扫描列表，再抓详情页校验发布时间与原始来源
- 备注: 适合快速发现当天热点，但成稿时要尽量回到原始来源链接

## 官方外的二级补充源

### Anthropic News

- URL: https://www.anthropic.com/news
- 类型: 官方新闻页
- 状态: 2026-03-29 `HTTP 200`
- 适用分类: 大模型、安全 / 治理、应用 / 产品
- 用法: 官方动态补充
- 备注: 频率不高，但一手价值高

### MIT Technology Review RSS

- URL: https://www.technologyreview.com/feed/
- 类型: RSS
- 状态: 2026-03-29 `HTTP 200`
- 适用分类: 大模型、安全 / 治理、商业趋势
- 用法: 从 RSS 中筛 AI 内容
- 备注: 深度报道优先，不适合追求大量快讯

### Google AI Blog

- URL: https://blog.google/innovation-and-ai/technology/ai/
- 类型: 官方栏目页
- 状态: 2026-03-29 `301 -> 200`
- 适用分类: 大模型、应用 / 产品、开发者工具
- 用法: 扫栏目页，再抓具体文章
- 备注: 原旧地址会跳转到新栏目页，引用时使用新地址

## 当前删除结果

截至 2026-03-29，这份清单里没有发现需要因“源站失效”而删除的新闻源。

当前只发现一个环境级问题：

- 本机在调用 `url-to-markdown` 时，日常 Chrome fallback 出现过本地 `ECONNREFUSED`，这是当前机器的浏览器调试端口 / bridge 状态问题，不是 `maomu`、`HubToday` 或 `The Verge` 源站不可用。

## 抓取顺序

推荐顺序：

1. 先扫官方一级优先源
2. 再扫官方 X / Twitter 渠道
3. 再拉 RSS 和媒体 / 聚合页
4. 把候选条目按分类放入临时池
5. 对信息不全的条目抓详情页
6. 最后进入搜索补漏

## 搜索补漏矩阵

官方源和媒体源之后，必须补搜索。不要只跑一轮宽泛 query。

### 官方优先名单

以下主体必须优先覆盖：

- OpenAI
- Anthropic
- Google AI / Google DeepMind
- xAI
- MiniMax
- 智谱 AI
- Kimi / Moonshot
- 阿里 AI / Qwen / 通义
- 腾讯 / 混元
- 火山引擎 / 方舟 / 豆包
- Manus

对这些主体，必须至少执行：

1. 一轮官网 / 官方域名定向检索
2. 一轮产品名定向检索
3. 一轮官方社媒补漏检索

### 大模型

- 中文 query:
  - `大模型 发布`
  - `模型 更新`
  - `推理 模型`
- 英文 query:
  - `LLM release`
  - `foundation model launch`
  - `reasoning model update`
- 重点 provider:
  - 官方域名优先: `openai.com,anthropic.com,blog.google,deepmind.google,x.ai,qwenlm.ai,zhipuai.cn,moonshot.cn,hunyuan.tencent.com,volcengine.com`
  - `tavily --intent news --freshness pd --count 8`
  - `brave --language en --country US --count 8`
  - 可选补充: `volc --date-after <date> --date-before <date> --count 8`

### Agent

- 中文 query:
  - `AI Agent`
  - `智能体 发布`
  - `自动化 助手`
- 英文 query:
  - `AI agent news`
  - `agentic workflow`
  - `AI automation launch`
- 重点 provider:
  - 官方域名优先: `openai.com,anthropic.com,x.ai,manus.im,minimaxi.com,moonshot.cn`
  - `tavily --intent news --freshness pd --count 8`
  - `bocha --count 8`
  - 可选补充: `volc --date-after <date> --date-before <date> --count 8`

### 融资 / 商业

- 中文 query:
  - `AI 融资`
  - `AI 收购`
  - `AI 商业合作`
- 英文 query:
  - `AI funding`
  - `AI acquisition`
  - `AI partnership`
- 重点 provider:
  - 先确认是否存在官方公告或公司博文，再补媒体报道
  - `techcrunch.com`、`theinformation.com`、`venturebeat.com` 定向检索
  - `tavily --intent news --domain-filter techcrunch.com,venturebeat.com --count 8`
  - `brave --language en --country US --count 8`
  - 可选补充: `volc --date-after <date> --date-before <date> --count 8`

### 安全 / 治理

- 中文 query:
  - `AI 安全`
  - `AI 监管`
  - `人工智能 治理`
- 英文 query:
  - `AI safety news`
  - `AI regulation`
  - `AI policy update`
- 重点 provider:
  - `tavily --intent news --freshness pd --count 8`
  - `brave --language en --country US --count 8`
  - 可选补充: `volc --date-after <date> --date-before <date> --count 8`

### 应用 / 产品

- 中文 query:
  - `AI 产品 发布`
  - `AI 功能 更新`
  - `AI 应用 上线`
- 英文 query:
  - `AI product launch`
  - `AI feature update`
  - `AI app release`
- 重点 provider:
  - 官方域名优先: `openai.com,anthropic.com,blog.google,x.ai,minimaxi.com,moonshot.cn,qwenlm.ai,hunyuan.tencent.com,volcengine.com,manus.im`
  - `tavily --intent news --freshness pd --count 10`
  - `bocha --count 10`
  - `brave --language en --country US --count 8`
  - 可选补充: `volc --date-after <date> --date-before <date> --count 8`

### 开源

- 中文 query:
  - `开源 模型`
  - `开源 AI 工具`
  - `开源 Agent 框架`
- 英文 query:
  - `open source AI model`
  - `open source agent framework`
  - `open source AI tool release`
- 重点 provider:
  - 官方域名优先: `qwenlm.ai,openai.com,anthropic.com,blog.google,zhipuai.cn`
  - `tavily --intent source_finding --domain-filter github.com,huggingface.co --count 8`
  - `brave --language en --count 8`
  - `bocha --count 8`

## Provider 使用细则

### Tavily

- 适合最新动态和站点定向补充
- 优先参数:
  - `--intent news`
  - `--freshness pd` 或 `--freshness pw`
  - `--domain-filter`
  - `--count 8` 到 `12`

### Volc

- 适合中文站点和自然日窗口
- 定位: 可选补充引擎，不是日报 workflow 的硬依赖
- 优先参数:
  - `--date-after`
  - `--date-before`
  - `--domain-filter`
  - `--count 8`

### Bocha

- 适合中文召回和中文站点补漏
- 限制:
  - 当前不会原生下推时间条件
- 规避方式:
  - 补词面日期 query，例如 `2026年3月29日 AI 融资`

### Brave

- 适合英文主流媒体和国际校验
- 优先参数:
  - `--language en`
  - `--country US`
  - `--count 8`
- 限制:
  - 当前时间过滤不原生下推，不能单独承担“今日新闻”判断

## 深度与广度的落地方式

这里不使用虚构的 `depth` / `breadth` 参数，而是按现有能力执行：

- 搜索广度:
  - 多 provider 并行
  - 每分类中英双 query
  - `--count` 提高到 8 到 12
  - 固定源 + 搜索源混合召回
- 搜索深度:
  - 对高价值站点补 `--domain-filter`
  - 对指定日期补 `--date-after/--date-before`
  - 对不支持时间下推的 provider 补词面日期 query
  - 对候选结果再抓详情页正文
