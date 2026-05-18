# 新闻源与数据规则

这份文档只定义来源入口、扫描范围、来源数据预期和不可用报告规则。来源入口由 skill 作者维护，执行时不判断入口可信度，不决定入口是否应该保留在清单中。

## 使用原则

1. 简报候选应覆盖四类来源：官网 / 官方发布入口、权威新闻网站、权威论坛 / 社区、新闻聚合网站。
2. 不删来源类型，不把任何一类写成可忽略；如果某类来源不可用，报告该来源类型覆盖不足。
3. 成稿条目必须具备标题、发布时间、来源 URL 和摘要所需内容。
4. 候选阶段先去重和筛选，不要对全部召回结果逐条核对字段；只对准备入稿的少量条目核对发布时间、摘要所需内容和来源 URL。
5. 来源入口默认可信；执行时只检查数据字段是否满足成稿要求，不判断来源真伪。
6. 固定来源不可访问、重定向异常、返回壳页面、挑战页、空页面、无正文或无发布时间时，报告来源不可用。

## 来源不可用时的报告

1. 固定来源不可访问、重定向异常、返回壳页面、挑战页、空页面或无正文时，记录来源名称、URL 和失败现象。
2. 条目无明确发布时间、来源 URL 或摘要所需内容时，标记候选字段不完整。
3. 来源不可用时，不在 `sources.md` 中定义绕路查找策略；执行结果应报告该来源需要维护者更新。

## 官网 / 官方发布入口

这一组覆盖品牌官网、官方博客、官方发布页、官方文档、官方社媒入口。

### OpenAI

- `https://help.openai.com/en/articles/9624314-model-release-notes`
- `https://help.openai.com/en/articles/6825453-chatgpt-release-notes`
- `https://openai.com/index/`
- 覆盖范围
  - 模型发布、ChatGPT 产品发布、官方公告。

### Anthropic

- `https://www.anthropic.com/news`
- `https://platform.claude.com/docs/en/release-notes/overview`
- 覆盖范围
  - 公司新闻、Claude / API release notes。

### Google AI / Gemini / DeepMind

- `https://blog.google/`
- `https://deepmind.google/`
- 覆盖范围
  - Gemini、Google AI、Gemma、DeepMind 官方发布。

### xAI

- `https://x.ai/`
- `https://grok.com/`
- 覆盖范围
  - Grok 和 xAI 官方发布。

### MiniMax

- `https://www.minimaxi.com/`
- 覆盖范围
  - MiniMax 官方发布。

### 智谱 AI

- `https://www.zhipuai.cn/zh/news`
- `https://www.zhipuai.cn/zh/research`
- 覆盖范围
  - 智谱新闻和研究动态。

### Kimi / Moonshot

- `https://moonshot.cn/`
- 覆盖范围
  - Kimi、Moonshot 官方发布。

### 阿里 AI / Qwen

- `https://qwenlm.github.io/zh/blog/`
- `https://github.com/QwenLM/Qwen/releases`
- `https://qwen.ai/`
- 覆盖范围
  - 用官方博客和 GitHub Releases。
  - `qwen.ai` 只作为品牌入口。

### 腾讯 AI / 混元

- `https://cloud.tencent.com/document/product/1729/104753`
- 覆盖范围
  - 腾讯混元文档和官方发布。

### 火山引擎 / 豆包 / 方舟

- `https://developer.volcengine.com/`
- `https://www.volcengine.com/`
- 覆盖范围
  - 豆包、方舟、火山引擎官方发布。

### DeepSeek

- `https://deepseek.com/`
- 覆盖范围
  - DeepSeek 官方发布。

## 权威新闻网站

这一组直接作为成稿来源，也用于交叉验证。

- `https://www.theverge.com/ai-artificial-intelligence`
  - 国际产品发布、行业动态
- `https://www.wired.com/feed/tag/ai/latest/rss`
  - 深度稿、趋势与治理
- `https://www.technologyreview.com/feed/`
  - 深度报道、安全 / 治理
- `https://techcrunch.com/`
  - 融资、创业、产品更新

## 权威论坛 / 社区

这一组用于发现话题、官方账号更新、高互动讨论和社区反馈。

- `Reddit`
  - 每次日报都要覆盖一次 Reddit 信号
  - 看官方 subreddit、官方账号和高互动讨论串
  - 记录社区热点、发布线索、官方更新和产品反馈

## 新闻聚合网站

这一组提供当天热点和漏报内容。

- `https://hex2077.dev/`
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
- 覆盖范围
  - Hugging Face Blog 新文章和发布时间。
  - GitHub 组织页最近更新的重点仓库、`Releases`、`Tags`、`Commits`。

## 来源数据边界

### 来源覆盖

- 中文来源、英文来源、官方发布入口和技术来源都要覆盖。
- 每个重要分类至少要有中文或英文来源线索。

### 官方来源

- 重点品牌优先使用官方域名、官方账号、官方博客、官方文档、GitHub Release、模型页或论文页。
- 官方入口不可访问时，报告来源不可用；不要把替代查找策略写进 `sources.md`。

### 社区和聚合入口

- Reddit、HubToday、Maomu 是固定来源入口。
- 社区和聚合入口的预期字段见“来源数据预期”。

## 最低覆盖要求

1. 中文来源、英文来源、官方发布入口和技术来源都要覆盖。
2. 每个重要分类至少保留中文或英文候选来源。
3. 对候选集中命中的重点品牌，至少使用一个官方来源或权威报道来源。
4. 每次都覆盖 Reddit、HubToday、Maomu。
5. 开源分类至少覆盖 Hugging Face Blog RSS、Hugging Face Blog 详情页、重点 AI 厂商 GitHub 组织页最近更新仓库。

## 来源数据预期

这组规则定义来源产物需要具备的数据形态，不定义工具选择或访问策略。

1. 官方发布页、官方博客、官方文档、GitHub Release、模型页和论文页应提供标题、URL、发布时间或版本发布时间、正文摘要或变更说明。
2. 权威报道页应提供标题、URL、发布时间和摘要所需内容。
3. 社区入口和聚合入口应提供标题、URL、展示时间或讨论时间、线索摘要。
4. 开源入口应提供项目名、仓库或模型页 URL、发布时间或 release / tag / commit 时间、变更摘要。
5. 候选条目的展示时间、聚合时间和讨论时间只能作为候选时间提示；成稿时间必须来自详情页、官方发布页、权威报道页、release、tag、commit、模型页或论文页。
6. 不能提取标题、URL、时间字段或摘要所需内容的条目，标记为候选字段不完整。
7. 不满足目标时间窗的条目，直接从成稿候选中删除。
