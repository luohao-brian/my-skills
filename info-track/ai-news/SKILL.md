---
name: ai-news
description: 从固定来源及 AIHOT 采集 AI 新闻，按规范化链接与标题去重，提供来源诊断并直接生成新闻列表。适用于 AI 日报、快讯和行业动态汇总。
metadata: {"openclaw":{"skillKey":"ai-news","emoji":"🗞️","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-news","requires":{"bins":["python3"]}}}
---

# AI 新闻采集

采集固定来源和 AIHOT 条目，保留来源诊断，按规范化 URL 与标题去重并直接渲染新闻列表。

## 执行

运行采集器并渲染新闻列表。采集器保留来源提供的标题、摘要和链接，逐来源折叠精确重复；渲染时再折叠跨来源的同一文章。来源失败只记录在 source 诊断中，不阻止其他来源继续采集。

```bash
python3 {baseDir}/scripts/ai_news.py collect --out candidates.json
python3 {baseDir}/scripts/ai_news.py render --input candidates.json > news-list.md
```

每次日报在工作区新建独立运行目录，存放本轮候选数据和简报，不复用上轮文件。更新已有文件前先完整读取，遇到覆盖保护时先补齐读取，不换工具绕过。

最终只发送新闻列表正文，内部工具错误和文件路径留在运行记录；影响内容的来源缺失用一句话说明。发送到飞书时省略原始邮箱，必要时写成 `name [at] example.com`。cron 的投递错误由宿主处理，不能声称仅靠此说明实现自动重试。

## 按需读取

- 需要查看 JSON 字段或成稿错误时读取 [输出结构](references/output-schema.md)。
- 核对固定来源时读取 [来源清单](references/sources.json)。
- 查看来源耗时、候选数或采集异常时读取 [来源诊断](references/source-diagnostics.md)。

保留去重后的新闻条目；只排除明确无关或误采的条目。渲染结果逐条保留来源标题、摘要和链接。

## 时间窗口

- 默认采集最近 72 小时；“今日 / 今天 / 最新 / 日报”未明确指定自然日时也用此窗口。
- 对来源当前返回的条目应用时间窗口；不为覆盖满 72 小时而翻页追溯。
- 明确指定自然日时传 `--date YYYY-MM-DD`，只采集该日。
- 时间窗口确定后，不因候选不足改变窗口。
- AIHOT `/api/v1/items` 只提供最近 7 天；超出范围的历史自然日采集会记录该来源失败，不补造历史条目。
