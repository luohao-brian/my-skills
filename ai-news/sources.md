# 新闻源与检索规则

这份文档只定义来源入口、扫描范围、搜索分工和使用方式。

## 使用原则

1. 官网、权威新闻网站、权威论坛、新闻聚合网站，都要扫描。
2. 不按来源做高低排序，也不把任何一类来源写成“可忽略”。
3. 每次日报都同时扫描：
   - 官网 / 官方发布入口
   - 权威新闻网站
   - 权威论坛 / 社区
   - 新闻聚合网站
4. 交叉验证直接按下面执行：
   - 重要条目同时检查官网详情页和权威新闻站详情页
   - 没有官网公告的条目，至少检查两个独立高质量详情页
   - 社区或聚合站命中的条目，继续追详情页、官网或权威新闻站正文
5. 每条进入成稿的新闻，都必须至少落到一个带明确发布时间的详情页、官方发布页或权威报道页。
6. 不把固定旧文章 URL 当新闻矩阵；新闻入口必须能持续发现新内容。

## 官网 / 官方发布入口

这一组覆盖品牌官网、官方博客、官方发布页、官方文档、官方社媒入口。

### OpenAI

- `https://help.openai.com/en/articles/9624314-model-release-notes`
- `https://help.openai.com/en/articles/6825453-chatgpt-release-notes`
- `https://platform.openai.com/docs/changelog`
- `https://openai.com/index/`
- 使用方式
  - 直接抓取失败时，改用官方域名定向搜索回源。

### Anthropic

- `https://www.anthropic.com/news`
- `https://docs.anthropic.com/en/release-notes/api`
- 使用方式
  - 同时检查 `news` 和 API release notes。

### Google AI / Gemini / DeepMind

- `https://blog.google/innovation-and-ai/technology/ai/`
- `https://blog.google/products/gemini/`
- `https://deepmind.google/blog/`
- 使用方式
  - 同时检查 Google Blog 和 DeepMind Blog。

### xAI

- `https://x.com/xai`
- `site:x.ai Grok`
- `site:grok.com Grok`
- 使用方式
  - 直接检查官方 X 账号和官方域名搜索结果。

### MiniMax

- `https://www.minimaxi.com/news`
- `site:minimaxi.com MiniMax`
- 使用方式
  - 检查新闻页。
  - 再补一轮官方域名定向搜索。

### 智谱 AI

- `https://www.zhipuai.cn/zh/news`
- `https://www.zhipuai.cn/zh/research`
- 使用方式
  - 同时检查 `news` 和 `research`。

### Kimi / Moonshot

- `https://platform.moonshot.cn/blog`
- `site:moonshot.cn Kimi OR Moonshot`
- 使用方式
  - 检查 blog。
  - 再补一轮官方域名定向搜索。

### 阿里 AI / Qwen

- `https://qwenlm.github.io/zh/blog/`
- `https://github.com/QwenLM/Qwen/releases`
- `https://qwen.ai/`
- `site:qwenlm.github.io Qwen`
- `site:github.com/QwenLM/Qwen releases`
- 使用方式
  - 检查官方博客和 GitHub Releases。
  - `qwen.ai` 只用于搜索回源和品牌定位。

### 腾讯 AI / 混元

- `https://cloud.tencent.com/document/product/1729/104753`
- `https://hunyuan.tencent.com/`
- `site:tencent.com 混元 OR Hunyuan`
- 使用方式
  - 检查文档页和官网。

### 火山引擎 / 豆包 / 方舟

- `site:developer.volcengine.com 豆包 OR 方舟 OR 火山引擎`
- `site:volcengine.com ARK OR 豆包`
- `https://www.volcengine.com/product/ark`
- 使用方式
  - 通过官方域名搜索发现新文章。
  - 不写死具体文章 URL。

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

## 权威论坛 / 社区

这一组用于发现话题、官方账号更新、高互动讨论和社区反馈。

- `Reddit`
  - 每次日报都要扫描一次
  - 先看官方 subreddit、官方账号和高互动讨论串
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

- `https://huggingface.co/blog/feed.xml`
  - 用于发现开源模型、开源工具、平台能力和社区发布
- `https://huggingface.co/blog`
  - 用于详情页和回源
- `https://github.com/trending`
  - 只看高热度开源项目和仓库变化
  - 不用它查重点厂商、重点模型、重点产品新闻

## 搜索引擎分工

### Tavily

- 宽召回
- 时效新闻
- 官方域名定向搜索
- 深度补漏

### Bocha

- 中文宽度补充
- 中文站点补漏
- 中文热点发现

### Brave

- 英文国际动态
- 英文交叉验证
- 官方品牌 / 官方社媒结果补查

## 最低覆盖要求

1. 至少使用 `tavily` 和 `bocha`。
2. 国际或英文动态补 `brave`。
3. 每个重要分类至少做一轮中文 query 和一轮英文 query。
4. 对重点品牌至少做一轮官方域名定向检索。
5. 每次日报都扫描 Reddit、HubToday、Maomu。
6. 开源分类要扫描 Hugging Face Blog RSS；需要补开源项目热度时再扫 GitHub Trending。

## 执行顺序

1. 先做结构化搜索，建立候选集。
2. 扫官网 / 官方发布入口。
3. 扫权威新闻网站。
4. 扫权威论坛 / 社区。
5. 扫新闻聚合网站。
6. 扫开源模型 / 开源项目入口。
7. 对进入成稿的条目抓详情页并补齐字段。
