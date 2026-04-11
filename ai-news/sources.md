# 新闻源与检索规则

这份文档只定义来源入口、扫描范围、搜索分工和使用方式。

## 使用原则

1. 每次都扫四类来源：官网 / 官方发布入口、权威新闻网站、权威论坛 / 社区、新闻聚合网站。
2. 不删来源类型，不把任何一类写成可忽略。
3. 成稿条目必须落到带明确发布时间的详情页、官方发布页或权威报道页。
4. 没有官网公告时，至少补两个独立详情页；社区和聚合站命中后，继续追官网或权威新闻站正文。
5. 长期低质量入口不保留在固定清单里，直接改用品牌官方域名搜索。
6. 不稳定入口直接用 `tavily` 搜索官方域名、品牌名、产品名。

## 官网 / 官方发布入口

这一组覆盖品牌官网、官方博客、官方发布页、官方文档、官方社媒入口。

### OpenAI

- `https://help.openai.com/en/articles/9624314-model-release-notes`
- `https://help.openai.com/en/articles/6825453-chatgpt-release-notes`
- `https://platform.openai.com/docs/changelog`
- `https://openai.com/index/`
- 使用方式
  - 用 Help Center release notes 和 `openai.com/index/`。
  - 用 `tavily` 搜索 `site:openai.com`。

### Anthropic

- `https://www.anthropic.com/news`
- `https://docs.anthropic.com/en/release-notes/api`
- 使用方式
  - 用 `news` 和 API release notes。

### Google AI / Gemini / DeepMind

- `https://blog.google/innovation-and-ai/technology/ai/`
- `https://blog.google/products/gemini/`
- `https://deepmind.google/blog/`
- 使用方式
  - 用 Google Blog 和 DeepMind Blog。
  - 用 `tavily` 搜索 `site:blog.google` 或 `site:deepmind.google`。

### xAI

- `https://x.com/xai`
- `site:x.ai Grok`
- `site:grok.com Grok`
- 使用方式
  - 用 `tavily` 搜索 `site:x.ai Grok` 或 `site:grok.com Grok`。

### MiniMax

- `site:minimaxi.com MiniMax`
- 使用方式
  - 用 `tavily` 搜索 `site:minimaxi.com MiniMax`。

### 智谱 AI

- `https://www.zhipuai.cn/zh/news`
- `https://www.zhipuai.cn/zh/research`
- 使用方式
  - 用 `news` 和 `research`。

### Kimi / Moonshot

- `site:moonshot.cn Kimi OR Moonshot`
- 使用方式
  - 用 `tavily` 搜索 `site:moonshot.cn Kimi OR Moonshot`。

### 阿里 AI / Qwen

- `https://qwenlm.github.io/zh/blog/`
- `https://github.com/QwenLM/Qwen/releases`
- `https://qwen.ai/`
- `site:qwenlm.github.io Qwen`
- `site:github.com/QwenLM/Qwen releases`
- 使用方式
  - 用官方博客和 GitHub Releases。
  - `qwen.ai` 只用于搜索回源和品牌定位。

### 腾讯 AI / 混元

- `https://cloud.tencent.com/document/product/1729/104753`
- `site:tencent.com 混元 OR Hunyuan`
- 使用方式
  - 用文档页。
  - 用 `tavily` 搜索 `site:tencent.com 混元 OR Hunyuan`。

### 火山引擎 / 豆包 / 方舟

- `site:developer.volcengine.com 豆包 OR 方舟 OR 火山引擎`
- `site:volcengine.com ARK OR 豆包`
- 使用方式
  - 用 `tavily` 搜索官方域名结果，不写死具体文章 URL。

### DeepSeek

- `https://www.deepseek.com/`
- `site:deepseek.com DeepSeek`
- 使用方式
  - 用 `tavily` 搜索 `site:deepseek.com DeepSeek`。
  - 官方正文拿不到时，用权威报道交叉验证。

## 权威新闻网站

这一组直接作为成稿来源，也用于交叉验证。

- `https://www.theverge.com/ai-artificial-intelligence`
  - 国际产品发布、行业动态
- `https://www.wired.com/feed/tag/ai/latest/rss`
  - 深度稿、趋势与治理
- `https://techcrunch.com/feed/`
  - 融资、创业、产品更新
- `https://www.technologyreview.com/feed/`
  - 深度报道、安全 / 治理
- 使用方式
  - 用 `tavily` 搜索站点结果，再打开详情页。

## 权威论坛 / 社区

这一组用于发现话题、官方账号更新、高互动讨论和社区反馈。

- `Reddit`
  - 每次日报都要覆盖一次 Reddit 信号
  - 看官方 subreddit、官方账号和高互动讨论串
  - 用 `tavily` 搜索相关 subreddit 结果页
  - 记录社区热点、发布线索、官方更新和产品反馈

## 新闻聚合网站

这一组用于发现当天热点和漏报。命中后继续追详情页、官网或权威新闻站正文。

- `https://ai.hubtoday.app/`
  - 每次日报都要扫描一次
  - 用于发现当天热点和漏报
- `https://maomu.com/news`
  - 每次日报都要扫描一次
  - 用于中文热点和快讯发现

## 开源模型 / 开源项目入口

这一组只看开源模型、SDK、工具链、论文配套代码和 release 更新，不用它查融资、产品商业化和官网公告。

- `https://huggingface.co/blog/feed.xml`
  - 用于发现开源模型、开源工具、平台能力和社区发布
- `https://huggingface.co/blog`
  - 用于详情页和回源
- 重点 AI 厂商 GitHub 范围
  - `https://github.com/openai`
  - `https://github.com/anthropics`
  - `https://github.com/google-deepmind`
  - `https://github.com/zai-org`
  - `https://github.com/minimax-ai`
  - `https://github.com/moonshotai`
  - `https://github.com/QwenLM`
  - `https://github.com/Tencent-Hunyuan`
  - `https://github.com/deepseek-ai`
  - `https://github.com/huggingface`
- 使用方式
  - 先扫 Hugging Face Blog 的新文章标题和发布时间，再打开详情页。
  - 再扫这些 GitHub 组织页最近更新的仓库。
  - 命中重点仓库后，再看 `Releases`、`Tags`、`Commits`。

## 搜索引擎分工

### Tavily

- 宽召回、时效新闻、官方域名搜索、补漏

### Bocha

- 中文补充、中文站点补漏、中文热点

### Brave

- 英文动态、英文交叉验证、官方品牌结果补查

## 最低覆盖要求

1. 至少用 `tavily` 和 `bocha`，英文动态补 `brave`。
2. 每个重要分类至少做一轮中文 query 和一轮英文 query。
3. 每个重点品牌至少做一轮官方域名搜索。
4. 每次都覆盖 Reddit、HubToday、Maomu。
5. 开源分类至少覆盖 Hugging Face Blog RSS、Hugging Face Blog 详情页、重点 AI 厂商 GitHub 组织页最近更新仓库。

## 执行顺序

1. 先做结构化搜索。
2. 再扫官网、新闻站、社区、聚合站、开源入口。
3. 最后抓详情页并补齐字段。
