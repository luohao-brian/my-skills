---
name: ai-news
description: 生成中文版 AI 新闻简报。消费高产新闻和聚合入口，按来源数据规则筛选候选、核对入稿字段，输出按分类组织的 markdown 日报。适用于 AI 日报、今日快讯、行业动态汇总和持续追踪最新进展。
homepage: https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-news
metadata: {"openclaw":{"skillKey":"ai-news","emoji":"🗞️","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-news","requires":{"anyBins":["python3","python"]}}}
---

# AI 新闻简报

产出中文版 AI 新闻简报。优先运行本 skill 自带脚本完成来源采集、候选筛选、合同校验和模板渲染；模型只在脚本标记需要审阅时补全分类、中文摘要或入稿判断。

执行依赖：

- [references/sources.json](references/sources.json)：可执行来源注册表
- [references/source-contract.md](references/source-contract.md)：来源字段和边界说明
- [references/output-schema.md](references/output-schema.md)：候选 JSON 和 coverage 合同
- [templates/brief.md.tpl](templates/brief.md.tpl)：最终简报模板
- [templates/item.md.tpl](templates/item.md.tpl)：单条新闻模板
- [templates/summarize-prompt.md.tpl](templates/summarize-prompt.md.tpl)：模型审阅模板

最小命令：

```bash
python3 {baseDir}/scripts/ai_news.py run --window 72h
python3 {baseDir}/scripts/ai_news.py collect --date YYYY-MM-DD --out candidates.json
python3 {baseDir}/scripts/ai_news.py validate --input candidates.json
python3 {baseDir}/scripts/ai_news.py render --input candidates.json
```

执行合同：

1. 优先运行 `scripts/ai_news.py run`。只有需要人工审阅或二次加工时，才拆成 `collect`、审阅 JSON、`validate`、`render`。
2. 脚本 stdout 只输出机器可消费 JSON 或最终 markdown；采集日志、来源失败和诊断信息写 stderr。
3. 采集结果必须包含 `window`、`source_coverage`、`candidates`、`excluded`、`missing`。
4. 入稿条目必须有 `title`、`published_at`、`source_url`、`summary_basis`、`category`、`zh_summary`。
5. 最终 markdown 必须由 `render` 读取候选 JSON 和模板生成，不手写结构。

## Agent 边界

1. [references/sources.json](references/sources.json) 中的固定来源是输入边界，不在执行中排序、替换或扩展。
2. 内容真实性不在 skill 内裁决；只检查字段是否满足成稿要求。
3. 来源不可用或字段不完整时，写入 `source_coverage` 和 `missing`，不要让上层从日志推断。
4. `candidate_count` 不是完成依据；只有通过 `validate` 的业务字段合同才可进入 `render`。

## 时间窗口

- 未指定日期、自然日或自然周时，目标时间窗是最近 `72` 小时。
- “今日 / 今天 / 昨日”按本地完整自然日计算，不按执行时刻截断。
- 目标时间窗确定后，不因候选不足而切换、扩展或回退；只说明覆盖不足。
- 发布时间写相对时间；有绝对时间时补在括号里。

## 分类

- 模型 / 研究
- Agent / 开发者工具
- 技术博客 / 工程实践
- 产品 / 应用
- 商业 / 融资
- 安全 / 治理

没有有效候选的分类可以省略；有有效候选的分类按篇幅规则保留代表性条目。

## 分类容量

以下区间只控制篇幅，未超上限不压缩。

- 模型 / 研究：18-28 条
- Agent / 开发者工具：12-20 条
- 技术博客 / 工程实践：6-10 条
- 产品 / 应用：18-30 条
- 商业 / 融资：4-7 条
- 安全 / 治理：6-10 条

去重合并同一 URL、转载或重复事件；同主题下的不同进展保持独立。

达到区间上限后，按来源、子主题和事件类型分散保留，再比较时间、重要性、字段完整性和重复度。

## 召回与入稿

优先利用入口中已有字段，避免把已召回的信息再压缩掉。

1. 字段完整、分类明确、中文摘要已补全的入口候选可以入稿。
2. 同一入口中的独立条目可以分别入稿。
3. 没有单条原文链接时，可以使用入口链接作为来源链接，并在 `summary_basis` 中保留依据。
4. 容量不足时先回看已读候选，不为补量放宽时间窗、来源或字段要求。
