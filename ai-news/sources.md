# 新闻源

这份文档列出可消费入口、字段取得位置和覆盖边界。日报扫描入口应能在入口页、Feed、JSON 或日期页的解码后内容中直接提供标题、发布时间 / 展示时间、来源 URL、摘要 / 描述 / 正文片段；只给标题或只给跳转链接的聚合入口不放进扫描入口。

日期页型入口的目标日期页不存在时，可以使用目标日期前后 `72` 小时内最近的已发布日期页建立候选；入稿仍按条目的发布时间、页面日期和目标时间窗筛选。

## 日报扫描入口

### 新闻 Feed

- `https://www.theverge.com/rss/ai-artificial-intelligence/index.xml`
  - 取数：Atom `<entry>`
  - 字段：`<title>`、`<link href>`、`<updated>`、`<content>` 或 `<summary>`
  - 覆盖：国际产品发布、行业动态、公司事件
- `https://www.wired.com/feed/tag/ai/latest/rss`
  - 取数：RSS `<item>`
  - 字段：`<title>`、`<link>`、`<pubDate>`、`<description>`
  - 覆盖：深度稿、趋势、安全与治理
- `https://www.technologyreview.com/feed/`
  - 取数：RSS `<item>`
  - 字段：`<title>`、`<link>`、`<pubDate>`、`<description>` 或 `<content:encoded>`
  - 覆盖：深度报道、模型行业动态、安全与治理
- `https://techcrunch.com/category/artificial-intelligence/feed/`
  - 取数：RSS `<item>`
  - 字段：`<title>`、`<link>`、`<pubDate>`、`<description>`
  - 覆盖：融资、创业、产品更新、公司事件

### 英文聚合 Feed

- `https://tensorfeed.ai/api/news`
  - 取数：JSON `articles[]`
  - 字段：`title`、`url`、`publishedAt`、`source` / `sourceDomain`、`snippet`、`categories`
  - 摘要：使用 `snippet` 中的自然语言内容；`snippet` 只有 `Article URL` / `Comments URL` / `Points` 时不满足摘要字段
  - 覆盖：模型、产品、研究、社区和工程动态
- `https://www.dailydoseofai.tech/rss.xml`
  - 取数：RSS `<item>`
  - 字段：`<title>`、`<link>`、`<pubDate>`、`<description>`
  - 覆盖：研究论文、Agent、开发者动态、社区热点
- `https://planet-ai.net/rss.xml`
  - 取数：RSS `<item>`
  - 字段：`<title>`、`<link>`、`<pubDate>`、`<description>`
  - 覆盖：AI 公司博客、研究实验室、开发者博客和技术新闻聚合

### 中文聚合页

- `https://maomu.com/news`
  - 取数：页面 HTML 和 Nuxt SSR 数据中的新闻列表
  - 字段：`title`、`sourceLink`、`publishedAtDate` + `publishedAt`、`subtitle`，页面卡片里的 `.title`、`.desc`、`.source-name` 也可使用
  - 覆盖：中文热点、快讯发现
- `https://daily.xiaohu.ai/`
  - 取数：先从首页最新卡片或归档卡片取得日期页；日期页形如 `https://daily.xiaohu.ai/YYYY-MM-DD/`；目标日期页不存在时，使用目标日期前后 `72` 小时内最近的已发布日期页
  - 字段：日期页 `.date-meta .date`，头条 `.headline-title` / `.headline-summary` / `.read-more`，列表 `.point-title a` / `.point-summary`，深度项 `.deep-title` / `.deep-summary`，分类项 `.cat-item-title` / `.cat-item-summary`
  - 覆盖：中文日报、产品发布、技术突破、行业观察
- `https://hex2077.dev/docs/`
  - 取数：按目标日期进入日报页，路径形如 `https://hex2077.dev/docs/YYYY-MM/YYYY-MM-DD/`；目标日期页不存在时，使用目标日期前后 `72` 小时内最近的已发布日期页
  - 字段：页面 `<title>` / canonical URL / `meta description` 提供日期与总摘要；正文段落中的加粗标题、链接和段落文本提供条目标题、来源 URL 和摘要内容
  - 覆盖：中文热点、AI 工具、模型发布、社区动向
- `https://www.littleworld.win/data/ai-news/arxiv-cs-ai-latest.json`
  - 取数：JSON `articles[]`
  - 字段：`title`、`date`、`summary`、`url`、`category`
  - 覆盖：arXiv CS.AI 论文、模型研究、工程研究
- `https://www.littleworld.win/data/ai-news/every-latest.json`
  - 取数：JSON `articles[]`
  - 字段：`title`、`date`、`summary`、`url`、`category`
  - 覆盖：AI 产品、创业、商业和行业分析
- `https://www.littleworld.win/data/ai-news/moltbook-latest.json`
  - 取数：JSON `articles[]`
  - 字段：`title`、`date`、`summary`、`url`、`category`
  - 覆盖：大模型行为、Agent、评测、产品和技术讨论

Littleworld 三个 JSON 入口彼此独立；某个 JSON 入口不可访问或响应体无法解析时，只记录该入口不可用，不影响其他 Littleworld 入口的候选。

## 定向取数入口

下面入口用于获取官网、官博和技术博客内容。按列出的页面和字段取数；这些页面应能直接提供成稿需要的标题、发布时间、来源 URL 和摘要内容。不要把这些入口扩展成未列页面、厂商矩阵或额外来源。

### 官网和技术博客入口

- `https://openai.com/news/rss.xml`
  - 取数：RSS `<item>`
  - 字段：`<title>`、`<link>`、`<pubDate>`、`<description>`、`<category>`
- `https://www.anthropic.com/news`
  - 取数：列表页 HTML / Next 数据
  - 字段：标题、文章 URL、发布时间、卡片描述；只收录摘要内容存在的条目
- `https://www.anthropic.com/engineering`
  - 取数：列表页 HTML / Next 数据
  - 字段：标题、文章 URL、发布时间、卡片描述；只收录摘要内容存在的条目
- `https://blog.google/innovation-and-ai/technology/ai/rss/`
  - 取数：RSS `<item>`
  - 字段：`<title>`、`<link>`、`<pubDate>`、`<description>`
- `https://deepmind.google/blog/rss.xml`
  - 取数：RSS `<item>`
  - 字段：`<title>`、`<link>`、`<pubDate>`、`<description>`
- `https://www.interconnects.ai/feed`
  - 取数：RSS `<item>`
  - 字段：`<title>`、`<link>`、`<pubDate>`、`<description>`
  - 覆盖：开源模型生态、模型发布、评测、训练和研究分析

## 入稿字段

- 标题：使用 Feed、列表卡片、日期页条目或文章标题。
- 发布时间：使用 Feed 时间、列表展示时间、日期页日期或文章发布时间。
- 来源 URL：使用 Feed 链接、列表卡片链接、日期页原文链接；没有单条原文链接时可使用聚合日期页链接。
- 摘要：使用 Feed 描述、列表卡片描述、日期页摘要、正文片段或文章开头摘要。
