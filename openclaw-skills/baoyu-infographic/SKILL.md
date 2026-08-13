---
name: baoyu-infographic
description: 分析内容并以布局×风格组合生成专业信息图和高密度视觉总结。用户要求信息图、可视化、视觉摘要、一图看懂或发布级信息大图时使用。
metadata: {"openclaw":{"skillKey":"baoyu-infographic","emoji":"🧩","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/baoyu-infographic"}}
---

# Baoyu Infographic

Pinned upstream content lives under `upstream/`. Keep it unchanged.

## Progressive routing

For generation, first read [`image tools`](references/upstream-sections/02-image-generation-tools.md), [`confirmation policy`](references/upstream-sections/04-confirmation-policy.md), [`output structure`](references/upstream-sections/10-output-structure.md), and [`core principles`](references/upstream-sections/11-core-principles.md). Load each `references/upstream-sections/12-workflow--step-*.md` only when reaching that step. Then read:

- [`upstream/references/analysis-framework.md`](upstream/references/analysis-framework.md)
- [`upstream/references/structured-content-template.md`](upstream/references/structured-content-template.md)
- [`upstream/references/base-prompt.md`](upstream/references/base-prompt.md)
- exactly one selected file under `upstream/references/layouts/`
- exactly one selected file under `upstream/references/styles/`

Read [`user input tools`](references/upstream-sections/01-user-input-tools.md) only when the source must be fetched. Read the option/gallery/recommendation section files only when the user has not fixed layout/style. Read `upstream/references/config/first-time-setup.md` only when no `EXTEND.md` preference exists.

Resolve every relative path from `upstream/`.

## Contract

Files under `references/upstream-sections/` are mechanically generated from the pinned upstream entrypoint; never edit them. Follow selected upstream rules without capability cuts. Use upstream `EXTEND.md` preferences; when the backend is `ark-image-gen`, read that installed skill. Apply the active runtime or user output path; this package defines none. Read [`UPSTREAM.json`](UPSTREAM.json) only for provenance or sync work.
