---
name: ai-tech-blogs
description: 从 Hubwiz 与 QingkeAI 采集连续 7 天内的 AI 技术博客候选并生成中文列表。适用于技术博客周报、工程实践阅读清单和 AI 技术文章聚合。
metadata: {"openclaw":{"skillKey":"ai-tech-blogs","emoji":"📚","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-tech-blogs","requires":{"bins":["python3"]}}}
---

# AI 技术博客聚合

运行采集器生成候选 JSON，并按输出格式生成中文列表。

读取规则：

- 生成列表前读取 [references/output-schema.md](references/output-schema.md)。
- 需要确认固定来源时读取 [references/sources.md](references/sources.md)。

```bash
python3 {baseDir}/scripts/tech_blogs.py --output tech-blog-candidates.json --stats
```

调用合同：

1. 仅使用可选的 `--date YYYY-MM-DD`、`--output` 和 `--stats`；未指定日期时不传 `--date`。
2. 候选 JSON 与列表格式遵循 [references/output-schema.md](references/output-schema.md)。

## 时间窗口

- 不传 `--date`：采集截至今天的最近 7 天。
- 传 `--date YYYY-MM-DD`：采集该日起连续 7 天。
- 单次窗口固定为 7 天；不因候选不足改变窗口。
