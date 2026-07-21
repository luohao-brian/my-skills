# 候选与成稿格式

顶层 JSON：

```json
{
  "kind": "ai-tech-blogs",
  "window": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
  "weights": {"Hubwiz": 0.75, "QingkeAI": 0.25},
  "limit": 50,
  "items": []
}
```

每个 `items[]` 包含 `title`、`url`、`summary`、`date`、`source`、`category`、`score`、`metadata`。

最终列表固定为：

```markdown
### 1. 中文标题

- 来源：Hubwiz
- 摘要：一句中文摘要。
- 时间：YYYY-MM-DD
- 链接：[原文](https://example.com)
```

单个来源失败时保留另一来源的有效结果，并明确说明实际来源数量；两者都为空时不扩窗、不补写。
