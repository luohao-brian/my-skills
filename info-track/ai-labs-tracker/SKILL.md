---
name: ai-labs-tracker
description: 按单次 7 天窗口采集 AI 厂商产品、API、工程、博客和研究更新。适用于生成 AI 厂商周报、月报，或追踪 OpenAI、Anthropic/Claude、Google/DeepMind、Cursor 等来源的阶段性动态。
metadata: {"openclaw":{"skillKey":"ai-labs-tracker","emoji":"🧪","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-labs-tracker","requires":{"bins":["python3"]}}}
---

# AI 厂商动态追踪

运行采集器生成候选 JSON，并按模板生成中文报告。

读取规则：

- 生成报告前读取 [references/output-schema.md](references/output-schema.md) 和 [references/template.md](references/template.md)。
- 需要确认来源范围时读取 [references/sources.md](references/sources.md)。

```bash
python3 {baseDir}/scripts/vendor_updates.py --output vendor-candidates.json --stats
```

调用合同：

1. 仅使用可选的 `--date YYYY-MM-DD`、`--output` 和 `--stats`；未指定绝对日期时不传 `--date`。
2. 候选 JSON 遵循 [references/output-schema.md](references/output-schema.md)，报告遵循 [references/template.md](references/template.md)。

## 时间窗口

- 用户未指定绝对日期时，采集截至今天的最近 7 天。
- 用户说“本周 / 这周 / 最新 / 周报”但未指定绝对日期时，仍采集截至今天的最近 7 天，不改为自然周。
- 用户指定 `YYYY-MM-DD` 时，采集该日起连续 7 天。
- 单次窗口固定为 7 天；不因候选不足改变窗口。
