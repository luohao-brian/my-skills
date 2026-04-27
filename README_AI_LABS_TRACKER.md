# README_AI_LABS_TRACKER

`ai-labs-tracker` 是一个编排型 skill，用于追踪 OpenAI、Anthropic 和 Google DeepMind 过去一段时间内的最新动态，并输出结构化中文追踪报告。

## 目录与入口

- skill：[`/Users/bytedance/Documents/my-skills/ai-labs-tracker/SKILL.md`](/Users/bytedance/Documents/my-skills/ai-labs-tracker/SKILL.md)
- 信息源说明：[`/Users/bytedance/Documents/my-skills/ai-labs-tracker/references/sources.md`](/Users/bytedance/Documents/my-skills/ai-labs-tracker/references/sources.md)
- 报告模板：[`/Users/bytedance/Documents/my-skills/ai-labs-tracker/references/template.md`](/Users/bytedance/Documents/my-skills/ai-labs-tracker/references/template.md)

## 适合什么时候用

- 想追踪 OpenAI、Anthropic、Google DeepMind 最近 7 天、30 天或 90 天动态
- 想整理月报、双周报或专题追踪
- 想把产品发布、技术工程更新、前沿研究按统一结构整理出来

## 能力范围

- 固定追踪三家重点实验室
- 默认时间窗口是过去 30 天
- 按“产品发布 / 技术与工程 / 前沿研究”分类
- 输出带链接、日期、摘要的结构化报告

## 运行依赖

这个 skill 本身不依赖单独 Rust CLI，但执行时通常会配合已有抓取/搜索能力：

- `my-fetch`：抓官网、博客正文
- `volc-websearch`：补充新闻检索和交叉验证
- 海外官网抓取时，如当前网络环境需要，补充代理参数

## 使用提醒

- 先读 [`sources.md`](/Users/bytedance/Documents/my-skills/ai-labs-tracker/references/sources.md)，再开始追踪
- 先按官方来源抓取，再用搜索结果补漏
- 只保留目标时间窗内的动态
- 输出时统一包含标题、链接、日期、摘要

## 验证建议

当前仓库还没有为 `ai-labs-tracker` 提供单独的 `scripts/<skill>/verify.sh`。改动这个 skill 时，至少做这些检查：

- 确认 [`SKILL.md`](/Users/bytedance/Documents/my-skills/ai-labs-tracker/SKILL.md) 的规则仍然和 `references/` 一致
- 确认两个参考文档链接都可读、标题和字段没有漂移
- 如果改了追踪流程或分类规则，手工按一个最近 7 天的小范围样例跑一遍
