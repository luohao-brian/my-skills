---
name: ai-labs-tracker
description: 采集并整理 AI 厂商的产品发布、功能更新、API/工程动态、技术博客和研究进展。适用于生成 AI 厂商周报/月报，或追踪 OpenAI、Anthropic/Claude、Google/DeepMind、Cursor 等官方更新。
metadata: {"openclaw":{"skillKey":"ai-labs-tracker","emoji":"🧪","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-labs-tracker","requires":{"anyBins":["python3","python"]}}}
---

# AI 厂商动态追踪

运行确定性采集器获取候选；由 agent 完成核验、去重和最终中文报告。

执行前按需读取：

- [references/sources.md](references/sources.md)：来源范围与采集边界。
- [references/output-schema.md](references/output-schema.md)：候选字段和失败语义。
- [references/template.md](references/template.md)：需要完整周报或月报时的成稿格式。

```bash
python3 {baseDir}/scripts/vendor_updates.py --days 7 --output vendor-candidates.json --stats
```

执行合同：

1. 默认采集截至今天的最近 7 天；用户明确指定日期或周期时再传 `--date`、`--days`。
2. 保持官方来源集合稳定，不因某个来源暂时失败而扩展到媒体或聚合站。
3. 读取候选 JSON，按 URL 和同一事件去重；剔除 `-misc`、无有效标题或无可访问链接的条目。
4. 最终只分为“AI 厂商产品更新”和“AI 厂商博客更新”，并统一使用模板中的列表格式。
5. 标题和摘要可改写为中文，但不得增加候选字段与原文无法支持的事实。

`LLM_API_KEY` 可选。存在时采集器会调用 OpenAI-compatible provider 辅助中文改写和分类；缺失时使用原始文本与规则分类，采集仍可运行。
