# AI 新闻输出

`collect` 默认采集最近 72 小时；明确指定自然日时传 `--date YYYY-MM-DD`。`--out` 指定候选文件。需要代理时在本次调用中传 `--http-proxy`、`--https-proxy` 和可选的 `--no-proxy`；代理参数不持久化，也不写入候选 JSON。

`collect` 输出一个 JSON 对象：

```json
{
  "window": {},
  "sources": {},
  "diagnostics": {},
  "candidates": []
}
```

`sources.<source_id>` 包含 `ok`、`count`、`raw`、`window_candidates`、`unique_articles`、`unique_urls`、`exact_duplicate_rows`、`name`、`kind`、`role`、`error`、`elapsed_seconds` 和 `timeout_seconds`。`window_candidates` 是时间过滤后的候选数；`ok: true, window_candidates: 0` 表示来源采集成功但窗口内没有候选。同一来源内相同“规范化 URL + 标题”的重复行在输出前折叠，并计入 `exact_duplicate_rows`。`role` 为 `media | aggregator | official`，用于区分媒体、聚合简报和厂商官方来源。`elapsed_seconds` 是该来源本次运行耗时；`timeout_seconds` 是该来源的独立硬超时，来源配置未指定时默认为 20 秒。

`diagnostics` 包含：

- `sources_configured`、`sources_ok`：固定来源配置数和成功数。
- `candidate_rows`、`unique_articles`、`exact_duplicate_rows`：窗口内候选行数、按“规范化 URL + 标题”去重的文章键数和精确重复行数。
- `unique_urls`、`shared_url_rows`：规范化 URL 数和共享落地页的额外行数。聚合日报中的多条不同新闻可以共享同一 URL，不据此合并。
- `by_source_role`：按来源角色汇总来源数与候选数；`window_candidates` 是该角色的候选数。只描述采样结构，不表示质量或影响力。

`candidates[]` 每条普通来源文章包含：

```json
{
  "title": "",
  "url": "",
  "summary": "",
  "source_id": "theverge-ai",
  "source": "The Verge AI",
  "source_role": "media",
  "published_at": "ISO-8601"
}
```

AIHOT 候选额外保留 `original_url`、`original_source`、`discovered_at` 和 `external_id`。其 `url` 是 AIHOT 条目链接；`original_url` 是第三方原文链接。AIHOT API 的 `mode=selected` 表示请求 AIHOT 的 selected 数据范围；采集器保留返回条目并使用 `by=published` 和本地窗口过滤。API 只有滚动 7 天可读。

`ai_news.py render` 直接使用采集数据输出新闻列表。它按规范化 URL 与标题折叠跨来源的精确重复，保留先采集到的标题、摘要与链接；列表顶部的条目数是去重后的数量。`diagnostics.candidate_rows` 仍记录各来源的候选行数。

采集器逐来源折叠精确重复；渲染时再折叠跨来源的精确重复。其余条目保持独立。

旧候选只含 `title`、`url`、`summary` 时仍可渲染；缺少来源归属时不按 URL 域名猜测来源。
