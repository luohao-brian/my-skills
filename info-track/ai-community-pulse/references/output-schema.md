# 采集结果结构

顶层对象包含：

```json
{
  "window": {"start": "ISO-8601", "end": "ISO-8601", "hours": 72},
  "sources": {
    "hackernews": {"ok": true, "count": 12, "selected": 5, "error": null}
  },
  "candidates": []
}
```

每个候选包含：

```json
{
  "title": "原始标题或市场问题",
  "url": "原始社区链接",
  "summary": "原始正文、tagline 或市场摘要的短摘录",
  "date": "ISO-8601 或 null",
  "source": "平台标识",
  "channel": "固定频道、账号、subreddit、节点或 Feed 名称",
  "topic": "models | agents | systems | semiconductors",
  "kind": "community | product | prediction_market",
  "metrics": {}
}
```

约束：

- `sources` 必须记录所有尝试的平台；失败不能静默丢弃。
- `count` 是读取到的原始条数，`selected` 是主题过滤后的候选数。
- `date: null` 表示平台榜单未提供可用发布时间。
- `prediction_market` 的 `metrics` 可包含 `probability`、`volume24hr`，但概率不得转述为事实。
- 不输出跨平台绝对分数、RRF、热度状态或可信度状态。
