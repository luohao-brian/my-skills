---
name: diagram-design
description: 创建品牌化的流程图、架构图、时序图、数据模型、统计图表和静态数据报告，并可重绘 Draw.io 或 Mermaid。用户需要精确的 HTML/SVG/PNG 图表、经营/KPI 报告、技术关系图或演示用图时使用。
metadata: {"openclaw":{"skillKey":"diagram-design","emoji":"📐","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/diagram-design","requires":{"anyBins":["python3","python"]}}}
---

# Diagram Design

Pinned upstream content lives under `upstream/`. Keep it unchanged.

## Progressive routing

Read only what the current task needs:

1. Choose a type with [`visual type guide`](references/upstream-sections/04-3-selection-semantic-pattern-then-visual-type--visual-type-guide-39.md), then read [`complexity budget`](references/upstream-sections/08-7-layout-spacing--complexity-budget-per-diagram.md), [`taste gate`](references/upstream-sections/10-9-pre-output-checklist-taste-gate.md), and [`output contract`](references/upstream-sections/13-12-output.md).
2. Read [`upstream/references/style-guide.md`](upstream/references/style-guide.md) and exactly one selected `upstream/references/type-*.md`. Read `semantic-patterns.md` only when behavior, state, enforcement, or risk carries the meaning.
3. Load only the needed primitive section under `references/upstream-sections/07-6-core-svg-primitives--*.md`. For an editorial page, read [`summary card pattern`](references/upstream-sections/09-8-summary-card-pattern.md) and use the nearest `upstream/assets/template*.html`.
4. For Draw.io or Mermaid input, read [`import routing`](references/upstream-sections/12-11-importing-an-existing-diagram-draw-io-and-mermaid.md), the matching `upstream/references/import-*.md`, and `output-spec.md`. Read `export.md` only when SVG or PNG is requested.
5. Read [`first-time setup`](references/upstream-sections/01-0-first-time-setup-style-guide-gate.md) only when the project has not already selected a skin. Do not copy setup prose into generated artifacts.

Resolve every relative path from `upstream/`.

## Contract

Files under `references/upstream-sections/` are mechanically generated from the pinned upstream entrypoint; never edit them. Follow selected upstream rules without capability cuts. Apply the active runtime or user output path; this package defines none. Run `upstream/scripts/self_check.py` on every HTML result. Read [`UPSTREAM.json`](UPSTREAM.json) only for provenance or sync work.
