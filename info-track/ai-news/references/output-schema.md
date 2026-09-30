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

`sources.<source_id>` 包含 `ok`、`count`、`raw`、`window_candidates`、`selected`、`unique_articles`、`unique_urls`、`exact_duplicate_rows`、`name`、`kind`、`role` 和 `error`。`window_candidates` 是时间过滤后的候选数；`count` 与 `selected` 暂时等于它，仅为兼容旧调用方，均不表示编辑入选数。`ok: true, window_candidates: 0` 表示来源采集成功但窗口内没有候选。同一来源内相同“规范化 URL + 标题”的重复行在输出前折叠，并计入 `exact_duplicate_rows`。`role` 为 `media | aggregator | official`，用于区分媒体、聚合简报和厂商官方来源。

`diagnostics` 包含：

- `sources_configured`、`sources_ok`：固定来源配置数和成功数。
- `candidate_rows`、`unique_articles`、`exact_duplicate_rows`：窗口内候选行数、按“规范化 URL + 标题”去重的文章键数和精确重复行数。
- `unique_urls`、`shared_url_rows`：规范化 URL 数和共享落地页的额外行数。聚合日报中的多条不同新闻可以共享同一 URL，不据此合并。
- `by_source_role`：按来源角色汇总来源数与候选数；`window_candidates` 是候选数，`selected` 是兼容旧输出的同值别名。只描述采样结构，不表示质量或影响力。

`candidates[]` 每条普通来源文章包含：

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

AIHOT 候选额外保留 `original_url`、`original_source`、`discovered_at` 和 `external_id`。其 `url` 是 AIHOT 条目链接；`original_url` 是第三方原文链接。AIHOT 的 API `mode=selected` 表示 AIHOT 自己的精选范围，不表示本 skill 已审核入选。采集器使用 `by=published` 和本地窗口过滤；API 只有滚动 7 天可读。

`editorial.py prepare` 输出的 `events.json` 包含原 `window`、`sources`、`diagnostics`，以及 `group_links[]` 和 `events[]`。`diagnostics.event_count` 是保守归并后的事件数，`grouped_rows` 是合并掉的候选行数；这两个数字不代表漏并率或精选质量。审核合同见 [editorial.md](editorial.md)。

`editorial.py summary-queue` 列出缺少完整摘要的事件 ID、标题、采集文本和原文链接。`category-queue` 列出已填常用栏目、但标题提示可能属于扩展栏目的事件；逐条复核后改 `review.category`，或填 `review.category_reviewed=true` 保留原栏目。新建栏目时同时填写 `category_label`。

`render --all-events` 在同一页显示全部未拒绝事件，每个栏目只出现一次，栏目内中文条目排在英文条目前。`pending` 不是拒绝，也不被当作已核验；审核状态只保存在事件 JSON。待核验事件可填 `review.display_title`、`review.display_summary` 和指向事件成员链接的 `review.display_summary_source_url`；这些字段不改变审核状态。缺少完整摘要、来源链接不属于事件成员或分类复核未完成时，渲染失败并报告事件 ID。

跨语言自动归并须有同一原文链接及两个具体英文标题锚点；其余同事件由 `merge` 记录人工确认。

旧候选只含 `title`、`url`、`summary` 时仍可渲染；缺少来源归属时不得生成来源热力图，也不得按 URL 域名猜测来源。
