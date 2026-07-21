# 候选输出

顶层 JSON：

```json
{
  "kind": "ai-vendor-updates",
  "window": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
  "items": []
}
```

每个 `items[]` 包含：

- `title`：原始标题或 provider 的中文改写标题。
- `url`：原文直达链接。
- `summary`：来源摘要或 provider 基于来源字段生成的中文摘要。
- `date`：`YYYY-MM-DD`；无法识别日期的条目不会进入窗口结果。
- `source`：固定来源名。
- `category`：`AI厂商产品更新`、`AI厂商博客更新` 或 `-misc`。
- `score`：兼容字段；厂商候选通常为 `0`。
- `metadata`：来源分类等机器可读辅助字段。

单个来源失败会输出 `FETCH_VENDOR_SKIPPED`，不会使其他来源失效。JSON 为空时如实报告，不放宽窗口或来源。
