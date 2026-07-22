# AI 新闻输出

`collect` 输出一个 JSON 对象：

```json
{
  "window": {},
  "sources": {},
  "candidates": []
}
```

`sources.<source_id>` 包含 `ok`、`count` 和 `error`。`ok: true, count: 0` 表示来源采集成功但窗口内没有候选。

`candidates[]` 每条文章只保留：

```json
{
  "title": "",
  "url": "",
  "summary": ""
}
```
