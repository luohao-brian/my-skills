---
name: ai-news
description: 从固定来源及 AIHOT 采集 AI 新闻，合并中英文重复报道，按事件主题分栏并生成中文优先的简报。适用于 AI 日报、快讯和行业动态汇总。
metadata: {"openclaw":{"skillKey":"ai-news","emoji":"🗞️","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-news","requires":{"bins":["python3"]}}}
---

# AI 新闻简报

采集候选，合并同一事件，保留去重后的有效新闻。按本期事件主题组织栏目；栏目不限于预设的五类。

## 执行

1. 运行 `collect` 和 `prepare`，检查来源状态及事件归并。审核前读取 [事件审核规则](references/editorial.md)。
2. 读取 [简报格式](references/brief-format.md)，按队列补齐有来源依据的完整摘要，复核可能被预设栏目遮住的主题。分批任务不得把 `category` 限定为五选一。
3. 两个队列均清空后运行 `render --all-events`。缺摘要、未归类或分类待复核时，按报出的事件 ID 修正后重跑。

```bash
python3 {baseDir}/scripts/ai_news.py collect --out candidates.json
python3 {baseDir}/scripts/editorial.py prepare --input candidates.json --out events.json
python3 {baseDir}/scripts/editorial.py summary-queue --input events.json --limit 25 --out summary-queue.json
python3 {baseDir}/scripts/editorial.py category-queue --input events.json --limit 25 --out category-queue.json
python3 {baseDir}/scripts/editorial.py render --all-events --input events.json --out brief.md
```

`summary-queue` 与 `category-queue` 每批写回 `events.json` 后重跑，直到 `total` 为零。相似事件的人工合并用 `editorial.py merge`；命令、字段和判断规则见 [事件审核规则](references/editorial.md)。只刊载逐项核验事件时，使用不带 `--all-events` 的 `render`。

每次运行都以本轮新生成的候选、事件队列和简报为准，不直接复用旧的运行产物。采集、审核和渲染只使用上述命令及 skill 规定的输出文件；不要调用 `write_file`、`execute_code`，不要创建 `inspect.py` 等临时分析文件或额外报告。只有确需执行 skill 定义的事件合并时，才生成本轮对应的 `pairs.json`，不得覆盖既有文件。最终消息只发送简报正文，不发送命令、进程、文件路径、内部校验器、执行进度或工具错误；发送到飞书前删除或脱敏所有原始邮箱地址（例如 `name [at] example.com`，或直接省略），遇到 `230028 / EMAIL_ADDRESS` 时只允许脱敏后重试一次。

## 按需读取

- 需要查看 JSON 字段或成稿错误时读取 [输出结构](references/output-schema.md)。
- 核对固定来源时读取 [来源清单](references/sources.json)。
- 分析来源覆盖或生成热力图时读取 [来源诊断](references/source-diagnostics.md)。

默认保留去重后的事件；只排除明确无关或误采的事件。完整页按栏目编排，每个事件刊载一次，组内保留全部来源链接，栏目内中文条目靠前。

## 时间窗口

- 默认采集最近 72 小时；“今日 / 今天 / 最新 / 日报”未明确指定自然日时也用此窗口。
- 明确指定自然日时传 `--date YYYY-MM-DD`，只采集该日。
- 时间窗口确定后，不因候选不足改变窗口。
- AIHOT `/api/v1/items` 只提供最近 7 天；超出范围的历史自然日采集会记录该来源失败，不补造历史条目。
