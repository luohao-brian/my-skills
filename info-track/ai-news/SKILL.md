---
name: ai-news
description: 采集固定来源在最近 72 小时或指定自然日内的 AI 新闻候选并生成中文简报。适用于 AI 日报、今日快讯、行业动态汇总和最新进展追踪。
metadata: {"openclaw":{"skillKey":"ai-news","emoji":"🗞️","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-news","requires":{"bins":["python3"]}}}
---

# AI 新闻简报

运行采集器生成候选 JSON，并按模板生成中文简报。

读取规则：

- 生成简报前读取 [references/output-schema.md](references/output-schema.md) 和 [references/brief-format.md](references/brief-format.md)。
- 需要确认固定来源时读取 [references/sources.json](references/sources.json)。

```bash
python3 {baseDir}/scripts/ai_news.py collect --out candidates.json
python3 {baseDir}/scripts/ai_news.py render --input candidates.json
```

调用合同：

1. `collect` 仅使用可选的 `--date YYYY-MM-DD` 和 `--out`；没有指定自然日时不传 `--date`。
2. `render` 读取 `collect` 生成的 JSON，并渲染其中的全部候选。

## 时间窗口

- 不传 `--date`：采集最近 72 小时。
- “今日 / 今天 / 最新 / 日报”未指定绝对日期或自然日时，仍采集最近 72 小时。
- 传 `--date YYYY-MM-DD`：只采集该自然日。
- 时间窗口确定后，不因候选不足改变窗口。
