# AI 新闻输出

`collect` 输出一个 JSON 对象：

```json
{
  "window": {},
  "sources": {},
  "diagnostics": {},
  "candidates": []
}
```

`sources.<source_id>` 包含 `ok`、`count`、`raw`、`selected`、`unique_articles`、`unique_urls`、`exact_duplicate_rows`、`name`、`kind`、`role` 和 `error`。`count` 与 `selected` 等价，用于兼容旧调用方；`ok: true, selected: 0` 表示来源采集成功但窗口内没有候选。同一来源内相同“规范化 URL + 标题”的重复行在输出前折叠，并计入 `exact_duplicate_rows`。`role` 为 `media | aggregator | official`，用于区分媒体、聚合简报和厂商官方来源。

`diagnostics` 包含：

- `sources_configured`、`sources_ok`：固定来源配置数和成功数。
- `candidate_rows`、`unique_articles`、`exact_duplicate_rows`：窗口内候选行数、按“规范化 URL + 标题”去重的文章键数和精确重复行数。
- `unique_urls`、`shared_url_rows`：规范化 URL 数和共享落地页的额外行数。聚合日报中的多条不同新闻可以共享同一 URL，不据此合并。
- `by_source_role`：按来源角色汇总来源数与候选数；只描述采样结构，不表示质量或影响力。

`candidates[]` 每条文章只保留：

```json
{
  "title": "",
  "url": "",
  "summary": "",
  "source_id": "openai-news",
  "source": "OpenAI News",
  "source_role": "official",
  "published_at": "ISO-8601"
}
```

旧候选只含 `title`、`url`、`summary` 时仍可渲染；缺少来源归属时不得生成来源热力图，也不得按 URL 域名猜测来源。
