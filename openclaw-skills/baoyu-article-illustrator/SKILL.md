---
name: baoyu-article-illustrator
description: 分析技术报告、博客和长文结构，识别需要视觉说明的位置，统一规划并生成文章插图，再更新 Markdown 图片引用。用户要求为文章配图、自动插图或补充架构、概念与流程说明时使用。
metadata: {"openclaw":{"skillKey":"baoyu-article-illustrator","emoji":"🖼️","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/baoyu-article-illustrator"}}
---

# Baoyu Article Illustrator

Pinned upstream content lives under `upstream/`. Keep it unchanged.

## Progressive routing

For a new illustration pass, first read [`image tools`](references/upstream-sections/02-image-generation-tools.md), [`batch policy`](references/upstream-sections/03-batch-generation-policy.md), [`confirmation policy`](references/upstream-sections/04-confirmation-policy.md), [`three dimensions`](references/upstream-sections/06-three-dimensions.md), and [`types`](references/upstream-sections/07-types.md). Load each `references/upstream-sections/09-workflow--step-*.md` only when reaching that step. Then read:

- [`upstream/references/workflow.md`](upstream/references/workflow.md)
- [`upstream/references/prompt-construction.md`](upstream/references/prompt-construction.md)
- [`upstream/references/usage.md`](upstream/references/usage.md)
- [`upstream/references/style-presets.md`](upstream/references/style-presets.md) only when the style is not fixed
- exactly one selected file under `upstream/references/styles/`

Read [`user input tools`](references/upstream-sections/01-user-input-tools.md) only when the source must be fetched, [`reference images`](references/upstream-sections/05-reference-images.md) only when references are supplied, and [`modification`](references/upstream-sections/11-modification.md) only for an existing illustration. Read `upstream/references/config/first-time-setup.md` only when no `EXTEND.md` preference exists.

Resolve every relative path from `upstream/`.

## Contract

Files under `references/upstream-sections/` are mechanically generated from the pinned upstream entrypoint; never edit them. Follow selected upstream rules without capability cuts. Use upstream `EXTEND.md` preferences; when the backend is `ark-image-gen`, read that installed skill. Apply the active runtime or user output path; this package defines none. Read [`UPSTREAM.json`](UPSTREAM.json) only for provenance or sync work.
