# AI 新闻输出合同

`scripts/ai_news.py collect` 生成候选 JSON，`validate` 校验候选 JSON，`render` 只渲染通过校验的 JSON。

## 顶层字段

```json
{
  "window": {},
  "source_coverage": [],
  "candidates": [],
  "excluded": [],
  "missing": []
}
```

## window

- `start`：ISO 8601 时间。
- `end`：ISO 8601 时间。
- `label`：面向读者的时间窗口标签。

## source_coverage

每个来源必须有一条 coverage：

- `source_id`
- `name`
- `status`：`ok`、`partial`、`failed` 或 `skipped`
- `raw_count`
- `candidate_count`
- `missing_reason`

## candidates

入稿候选字段：

- `id`
- `title`
- `published_at`
- `published_display`
- `source_url`
- `source_id`
- `summary_basis`
- `category`
- `zh_summary`
- `needs_model_review`

`render` 只渲染 `needs_model_review=false` 且必填字段完整的候选。

## excluded

被过滤条目字段：

- `title`
- `source_url`
- `source_id`
- `reason`

常见 reason：`outside_window`、`not_ai_related`、`duplicate`、`missing_required_fields`。

## missing

字段缺失或来源失败字段：

- `source_id`
- `url`
- `missing_fields`
- `reason`
