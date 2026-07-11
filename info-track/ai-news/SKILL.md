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

脚本能力：

```bash
python3 {baseDir}/scripts/ai_news.py collect --window 72h --out candidates.json
python3 {baseDir}/scripts/ai_news.py render --input candidates.json
```

- `collect --source <source_id>` 可将采集范围限定为指定来源，参数可重复传入。
- `collect --limit-per-source <count>` 可设置每个来源保留的候选上限；未传入时不设上限。
- `render` 默认渲染全部候选。`--limit <count>` 和 `--offset <index>` 可选取指定范围；`--compact` 可切换紧凑视图，`--show-index` 可显示候选索引。

执行：

1. 先读取 `references/sources.json`，列出全部 `source_id`，建立 source 覆盖清单。
2. 使用 `collect` 生成候选 JSON，并根据任务需要决定是否限定来源或候选数量。
3. 使用 `render` 将候选 JSON 转成阅读素材；是否切分范围、显示索引或使用紧凑视图由当前任务决定。
4. 按本文件的成稿规则和 `references/brief-format.md` 输出最终 markdown。

## 来源与候选

1. `references/sources.json` 是唯一来源注册表；按其中的全部 `source_id` 建立 source 覆盖清单。
2. 来源集合以注册表为准；执行中保持来源集合和顺序稳定。
3. `kind` 只表示来源格式。
4. 脚本输出的文章候选只保留 `title`、`url`、`summary`。
5. `render` 只把候选 JSON 渲染成阅读素材，不使用外部模板生成最终简报。

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
