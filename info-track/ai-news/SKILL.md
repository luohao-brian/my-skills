---
name: ai-news
description: 采集固定来源及 AIHOT 精选入口的 AI 新闻，联合归并中英文重复报道并生成中文优先的资讯清单。适用于 AI 日报、今日快讯、行业动态汇总和最新进展追踪。
metadata: {"openclaw":{"skillKey":"ai-news","emoji":"🗞️","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-news","requires":{"bins":["python3"]}}}
---

# AI 新闻简报

运行采集器生成候选 JSON，归并同一事件的中英文报道，按中文优先输出去重清单。

读取规则：

- 生成简报前读取 [references/output-schema.md](references/output-schema.md) 和 [references/brief-format.md](references/brief-format.md)。
- 需要确认固定来源时读取 [references/sources.json](references/sources.json)。
- 逐事件审核前读取 [references/editorial.md](references/editorial.md)。
- 分析来源覆盖或生成热力图时读取 [references/source-diagnostics.md](references/source-diagnostics.md)。

```bash
python3 {baseDir}/scripts/ai_news.py collect --out candidates.json
python3 {baseDir}/scripts/editorial.py prepare --input candidates.json --out events.json
# 核对相似事件后，可用 merge --input events.json --pairs pairs.json --out events.json 合并
# 审核跨语言同事件；不相关的事件可在 review.decision 标记 reject
python3 {baseDir}/scripts/editorial.py summary-queue --input events.json --limit 25 --out summary-queue.json
# 分批处理：先用已采集的正文提炼，材料不足时再读原始链接；写入 review.display_summary 和 display_summary_source_url，直到队列清空
python3 {baseDir}/scripts/editorial.py render --all-events --input events.json --out brief.md
```

目标网络需要代理时，在同一次采集命令中显式传入：

```bash
python3 {baseDir}/scripts/ai_news.py collect \
  --http-proxy <proxy-url> \
  --https-proxy <proxy-url> \
  --no-proxy <comma-separated-hosts> \
  --out candidates.json
```

调用合同：

1. `collect` 使用可选的 `--date YYYY-MM-DD`、`--out`、`--http-proxy`、`--https-proxy` 和 `--no-proxy`；没有指定自然日时不传 `--date`。
2. `editorial.py prepare` 从候选生成事件，保守自动归并中英文报道；`merge` 记录额外确认的同事件对。`summary-queue` 分页列出尚缺来源对应摘要的事件，同一原文链接只给出一份采集文本；先利用采集文本成句，信息不足时再读取原文，逐批写回并重跑队列。`render --all-events` 为全部未标记 `reject` 的事件按栏目编排，每个栏目只出现一次，栏目内中文条目靠前，组内全部来源保留；缺摘要会报错。栏目可按事件内容扩展，没有每栏条数上限。`render` 不带此参数时只刊载已核验且标记 `select` 的事件。原有 `ai_news.py render` 仅用于查看全部原始候选。
3. 代理参数只作用于本次采集进程，不持久化、不写入候选 JSON，也不读取 Agent 专属代理配置；`localhost`、`127.0.0.1` 和 `::1` 始终绕过代理。需要代理时必须在唯一一次 `collect` 调用中显式传入。

## 时间窗口

- 不传 `--date`：采集最近 72 小时。
- “今日 / 今天 / 最新 / 日报”未指定绝对日期或自然日时，仍采集最近 72 小时。
- 传 `--date YYYY-MM-DD`：只采集该自然日。
- 时间窗口确定后，不因候选不足改变窗口。
- AIHOT `/api/v1/items` 只提供最近 7 天；超出范围的历史自然日采集会记录该来源失败，不补造历史条目。
