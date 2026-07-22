# 候选输出

顶层 JSON：

```json
{
  "kind": "ai-vendor-updates",
  "window": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "period": "1w"},
  "sources": {
    "OpenAI News": {"ok": true, "count": 2, "selected": 2, "error": null},
    "Anthropic News": {"ok": false, "count": 0, "selected": 0, "error": "TimeoutError"}
  },
  "items": []
}
```

`sources` 固定包含全部来源。`ok` 区分采集成功与失败；`count` 是该来源在窗口内的候选数；`selected` 是脚本按 URL 去重后的输出数；`error` 只在失败时记录异常类型。`ok: true, count: 0` 表示采集成功但窗口内没有更新。

每个 `items[]` 包含：

- `title`：原始标题或 provider 的中文改写标题。
- `url`：原文直达链接。
- `summary`：来源摘要或 provider 基于来源字段生成的中文摘要。
- `date`：`YYYY-MM-DD`；无法识别日期的条目不会进入窗口结果。
- `source`：固定来源名。
- `category`：`AI厂商产品更新`、`AI厂商博客更新` 或 `-misc`。
- `score`：兼容字段；厂商候选通常为 `0`。
- `metadata`：来源分类等机器可读辅助字段。
