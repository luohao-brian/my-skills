# README_AI_NEWS

`ai-news` 是一个面向 OpenClaw / `my-cowork` 的编排型 skill，用于生成中文版 AI 新闻简报。它不自带单独 CLI，而是组合固定新闻源与 `volc-websearch` 的多引擎检索能力来完成日报整理。

## 目录与入口

- skill：[`/Users/hluo/Documents/my-skills/ai-news/SKILL.md`](/Users/hluo/Documents/my-skills/ai-news/SKILL.md)
- 新闻源配置：[`/Users/hluo/Documents/my-skills/ai-news/sources.md`](/Users/hluo/Documents/my-skills/ai-news/sources.md)
- 输出格式：[`/Users/hluo/Documents/my-skills/ai-news/format.md`](/Users/hluo/Documents/my-skills/ai-news/format.md)
- 仓库级验证：[`/Users/hluo/Documents/my-skills/scripts/ai-news/verify.sh`](/Users/hluo/Documents/my-skills/scripts/ai-news/verify.sh)

## 安装

### my-cowork GitHub 安装

```bash
skills add https://github.com/luohao-brian/my-skills --skill ai-news
```

更新：

```bash
skills update https://github.com/luohao-brian/my-skills --skill ai-news
```

### OpenClaw / 本地 Agent

直接复制 [`/Users/hluo/Documents/my-skills/ai-news`](/Users/hluo/Documents/my-skills/ai-news) 到技能目录即可。

## 输出约束

- 结果必须是 markdown
- 必须按分类组织
- 每条新闻必须包含标题、摘要、发布时间、来源链接
- 中文成稿，但尽量保留原始来源链接

## 验证

静态校验：

```bash
cd /Users/hluo/Documents/my-skills
bash scripts/ai-news/verify.sh
```

带在线源检查：

```bash
cd /Users/hluo/Documents/my-skills
bash scripts/ai-news/verify.sh --live
```
