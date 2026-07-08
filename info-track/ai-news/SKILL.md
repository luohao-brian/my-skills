---
name: ai-news
description: 采集固定 AI 新闻源并输出候选文章。适用于生成 AI 日报、今日快讯、行业动态汇总和持续追踪最新进展。
homepage: https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-news
metadata: {"openclaw":{"skillKey":"ai-news","emoji":"🗞️","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-news","requires":{"anyBins":["python3","python"]}}}
---

# AI 新闻简报

运行脚本从固定来源采集 AI 新闻候选，并把候选渲染成便于阅读的素材。脚本只输出 `title`、`url`、`summary`；分类、筛选、去重、标题翻译、摘要改写和最终中文简报由 agent 完成。

执行依赖：

- [references/sources.json](references/sources.json)：可执行来源注册表
- [references/output-schema.md](references/output-schema.md)：输出字段
- [references/brief-format.md](references/brief-format.md)：最终 markdown 格式

采集规划：

```bash
# 对每个 source_id 单独采集，保留量由目标稿件规模决定
python3 {baseDir}/scripts/ai_news.py collect --window 72h --source <source_id> --limit-per-source <candidate_budget> --out candidates/<source_id>.json

# 对每个 source 文件分页阅读；offset 按 page_size 递增
python3 {baseDir}/scripts/ai_news.py render --input candidates/<source_id>.json --limit <page_size> --offset <offset> --show-index
python3 {baseDir}/scripts/ai_news.py render --input candidates/<source_id>.json --limit <page_size> --offset <offset> --compact --show-index
```

执行：

1. 先读取 `references/sources.json`，列出全部 `source_id`，建立 source 覆盖清单。
2. 根据目标简报规模给每个 source 分配 `candidate_budget`；高产 source 可提高预算，低产 source 保持完整覆盖。
3. 按 source 单独运行 `collect`，每个 source 写一个 `candidates/<source_id>.json`。
4. 对每个 source 文件用 `render --limit/--offset` 分页阅读；保留候选索引，便于回看和去重。
5. 按本文件的成稿规则和 `references/brief-format.md` 输出最终 markdown。

## 来源与候选

1. `references/sources.json` 是唯一来源注册表；按其中的全部 `source_id` 建立 source 覆盖清单。
2. 来源集合以注册表为准；执行中保持来源集合和顺序稳定。
3. `kind` 只表示来源格式。
4. 脚本输出的文章候选只保留 `title`、`url`、`summary`。
5. `render` 只把候选 JSON 渲染成阅读素材，不使用外部模板生成最终简报。
6. `xiaohu-daily` 是聚合型日报源（非原始新闻），其日期归档页可能不连续发布；当 `collect` 返回 0 条候选时，agent 应从首页 `https://daily.xiaohu.ai/` 用 `web_fetch` 读取最新可用日期链接，再用该日期重新运行 `collect --date <YYYY-MM-DD>`。
7. `xiaohu-daily` 的候选属于转载聚合，不单独计入原始来源覆盖；agent 在去重时应优先保留原始新闻 URL，`xiaohu-daily` 的条目仅作为补充索引和选题参考。

## 成稿规则

1. 读取一个或多个 `collect` 产出的 `candidates[]`，按候选的 `title`、`summary`、`url` 判断主题。
2. 合并同一 URL、转载或重复事件；同主题下的不同进展保持独立。
3. 将英文标题和摘要改写成中文。
4. 固定来源默认可信，不做来源质量打分；剔除明显非 AI、纯导航、纯推广、缺少有效摘要或无法定位事件主体的候选。
5. 优先保留模型发布、研究进展、Agent / 开发者工具、重要产品发布、融资并购、安全治理事件。
6. 不为补量放宽时间窗、来源或字段要求。

分类：

- 模型 / 研究：18-28 条
- Agent / 开发者工具：12-20 条
- 技术博客 / 工程实践：6-10 条
- 产品 / 应用：18-30 条
- 商业 / 融资：4-7 条
- 安全 / 治理：6-10 条

达到分类上限后，按来源、子主题和事件类型分散保留，再比较时间、重要性、字段完整性和重复度。

## 边界

1. 固定来源是输入边界，固定时间窗是时间边界。
2. 脚本负责采集和候选渲染；agent 负责分类、筛选、去重、翻译、改写和成稿。

## 时间窗口

- 默认目标时间窗是最近 `72` 小时。
- 用户说“今日 / 今天 / 最新 / 日报”但未指定绝对日期或自然日时，仍使用最近 `72` 小时。
- 只有用户明确指定绝对日期 `YYYY-MM-DD` 或明确要求自然日时，才使用 `--date YYYY-MM-DD`。
- 目标时间窗确定后，不因候选不足而切换、扩展或回退。
