---
name: ppt-master
description: 将 PDF、DOCX、PPTX、网页、Markdown、新闻或主题资料生成可编辑 SVG/PPTX 演示文稿，也可填充模板、美化既有 PPTX、添加动画与旁白。用户要求创建、制作、优化、检查或导出 PPT/演示文稿，提到 ppt-master，或需要 SVG 页面与 PowerPoint 互转时使用。
metadata: {"openclaw":{"skillKey":"ppt-master","emoji":"📊","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ppt-master","primaryEnv":"ARK_AGENT_PLAN_API_KEY","requires":{"anyBins":["python3","python"]}}}
---


# PPT Master Skill

PPT Master is a routed presentation workflow. This entry owns global execution discipline and route selection only; each selected route owns its procedure.

## Downstream Runtime Boundary

This OpenClaw/Hermes distribution follows upstream authoring, font selection, validation, and export. Read [`references/runtime.md`](references/runtime.md) for project directories, dependency/capability discovery, and Agent Plan media execution.

## Mandatory Load Order

1. Read this file.
2. Read [`references/runtime.md`](references/runtime.md) for the environment and media contracts.
3. Read [`workflows/routing.md`](workflows/routing.md).
4. Select exactly one top-level route and its active profile from the routing authority.
5. Read only the resulting runtime authority and its explicitly triggered supporting documents.

| Selected route / profile | Runtime authority |
|---|---|
| Generate PPTX — Image to PPTX | [`workflows/profiles/image-to-pptx.md`](workflows/profiles/image-to-pptx.md); Codex-supported, always Quick |
| Generate PPTX — Beautify | [`workflows/profiles/beautify-pptx.md`](workflows/profiles/beautify-pptx.md); explicit Quick intent selects Quick, otherwise Default |
| Generate PPTX — ordinary Default | [`workflows/generate-pptx.md`](workflows/generate-pptx.md) |
| Generate PPTX — ordinary explicit Quick | [`workflows/profiles/quick-generate.md`](workflows/profiles/quick-generate.md) |
| Create Template | [`workflows/create-template.md`](workflows/create-template.md) |
| Edit Native PPTX | [`workflows/edit-native-pptx.md`](workflows/edit-native-pptx.md) |

**Hard rule — selected authority only**: Do not load another top-level route's
procedure after routing. Image to PPTX and Beautify are mutually exclusive;
Image to PPTX activates Quick, while Beautify selects from explicit Quick
intent. Never load both runtimes. Supporting documents refine one route; they
never compete with it.

---

## Authored Expression Range

**Reference — not a constraint**: what a generated page can carry. Text — inline
emphasis runs, lead-in, kicker, pull quote, hero number, takeaway line. Geometry
— 187 Office presets, Boolean merge, connectors, freeform, page-field and
outline-carrier composition. Image — full-bleed field, editorial crop, shaped
picture, registered layers, scrim and spotlight, cross-page continuity. Paint —
gradients, channel alpha, native shadow and glow, halftone, faceted form.
Recurrence — one cross-page motif varied by page role. Each form's syntax lives
in the selected runtime authority's construction references.

---

## Phase Frame

Every route is one Plan → Do·Check·Act cycle: Plan ends when every authoring
input exists as a file or retained decision; Do authors pages, Check runs the
route's gates, Act repairs at the owning layer (discipline 7), and the cycle
ends at export. Step numbers stay as written.

| Phase | Default | Quick | Edit Native | Create Template |
|---|---|---|---|---|
| **Plan** | Steps 1–5 | §2 | §1–4 | Steps 1–3 |
| **Do·Check·Act** | Steps 6–7 | §3–4 | §5–7 | Steps 4–8 |

## Global Execution Discipline

1. **Serial execution** — Follow the selected authority's steps in order. A completed non-blocking step may continue directly to the next eligible step.
2. **Blocking means stop** — At every `⛔ BLOCKING` gate, wait for explicit user confirmation. Do not decide on the user's behalf.
3. **No cross-phase bundling** — Do not combine work across an unclosed gate. Once the route's final user gate closes, later non-blocking steps may continue automatically.
4. **Gate before entry** — Verify every listed prerequisite before entering a step.
5. **No speculative execution** — Do not prepare later-phase artifacts before their owning step.
6. **Deterministic routing** — Do not add a route-choice question when [`routing.md`](workflows/routing.md) resolves the request. If a route prerequisite is missing, state it and stop that route.
7. **Act at the owning layer** — On failure, repair at the shallowest layer that owns the fault: the page for a page-local issue, the Plan artifact for a roster/spec/resource fault, the owning source artifact for a tool failure; then resume from the route's declared pointer. Do not silently downgrade a required artifact.

## Global Communication Rules

- Match the user's language and source language unless the user explicitly overrides it.
- Localize user-facing option labels and explanations. Keep exact enum IDs or field names when needed for precision.
- Keep `design_spec.md` section headings and field names in the template's original English; content values may use the user's language.
- Before switching roles, read the corresponding role reference and output:

```markdown
## [Role Switch: <Role Name>]
📖 Reading role definition: references/<filename>.md
📋 Current task: <brief description>
```

---

## Repository Compatibility

- This package is a workflow/skill, not a generic application scaffold. Do not create `.worktrees/`, `tests/`, branch workflows, or generic engineering structure by default.
- Keep required workflow, reference, script, and template documentation inside this Skill directory.
- Repository-level documents may point into the package; package runtime files must not depend on repository-level instructions.
- On Windows, if a documented `python3 ...` command is unavailable, rerun the same command with `python`.
- Sponsor information is optional reference material. Read the matching [`SPONSORS.md`](SPONSORS.md) or [`SPONSORS_CN.md`](SPONSORS_CN.md) only when the user explicitly requests a model, AI image model, API/provider, or hosted-service recommendation. Never surface sponsor or model recommendations proactively during normal generation, troubleshooting, or quality review.
