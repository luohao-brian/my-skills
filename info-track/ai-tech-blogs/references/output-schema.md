# 候选与成稿格式

顶层 JSON：

```json
{
  "kind": "ai-tech-blogs",
  "window": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "period": "1w"},
  "sources": {
    "Hubwiz": {"ok": true, "count": 12, "selected": 12, "error": null},
    "QingkeAI": {"ok": false, "count": 0, "selected": 0, "error": "TimeoutError"}
  },
  "items": []
}
```

每个 `items[]` 包含 `title`、`url`、`summary`、`date`、`source`、`category`、`score`、`metadata`。

`sources.<source>.ok` 区分采集成功与失败；`count` 是来源在窗口内返回的候选数；`selected` 是按精确 URL 去重后的输出数；`error` 只在失败时记录异常类型。

最终列表固定为：

```markdown
### 1. 中文标题

- 来源：Hubwiz
- 摘要：一句中文摘要。
- 时间：YYYY-MM-DD
- 链接：[原文](https://example.com)
```
