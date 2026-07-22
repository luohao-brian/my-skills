---
name: ai-oss-models
description: 筛选连续 7 天内有动向的热门或重点 Hugging Face 开源模型与数据集，生成旗舰模型、本地部署、可复现项目和高质量数据集报告。适用于 AI 开源生态周报和指定日期窗口追踪。
metadata: {"openclaw":{"skillKey":"ai-oss-models","emoji":"🧩","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-oss-models","requires":{"bins":["python3"]}}}
---

# AI 开源模型观察

运行采集器生成候选 JSON，并按固定格式生成中文报告。

读取规则：

- 读取候选 JSON 前读取 [references/output-schema.md](references/output-schema.md)。
- 生成报告前读取 [references/format.md](references/format.md)。
- 需要确认分类字段时读取 [references/sources.md](references/sources.md)。

```bash
python3 {baseDir}/scripts/open_source_updates.py --output oss-candidates.json --stats
```

调用合同：

1. 仅使用可选的 `--date YYYY-MM-DD`、`--output` 和 `--stats`；未指定日期时不传 `--date`。
2. 候选 JSON 遵循 [references/output-schema.md](references/output-schema.md)，最终报告遵循 [references/format.md](references/format.md)。

## 时间窗口

- 不传 `--date`：采集截至今天的最近 7 天。
- 传 `--date YYYY-MM-DD`：采集该日起连续 7 天。
- 单次窗口固定为 7 天；不因候选不足改变窗口。
