---
name: ppt-master
description: 将 PDF、DOCX、PPTX、网页、Markdown、新闻或主题资料生成可编辑 SVG/PPTX 演示文稿，也可填充模板、美化既有 PPTX、添加动画与旁白。用户要求创建、制作、优化、检查或导出 PPT/演示文稿，提到 ppt-master，或需要 SVG 页面与 PowerPoint 互转时使用。
metadata: {"openclaw":{"skillKey":"ppt-master","emoji":"📊","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ppt-master","primaryEnv":"ARK_AGENT_PLAN_API_KEY","requires":{"anyBins":["python3","python"],"env":["ARK_AGENT_PLAN_API_KEY"]}}}
---


# PPT Master Skill

PPT Master is a routed presentation workflow. This entry owns global execution discipline and route selection only; each selected route owns its procedure.

## Downstream Runtime Boundary

This OpenClaw/Hermes distribution keeps upstream workflow semantics and routes while delegating environment-specific behavior to [`references/runtime.md`](references/runtime.md). The runtime contract has precedence only for project directories, target-host fonts, dependency/capability discovery, and the downstream release gate.

## Mandatory Load Order

1. Read this file.
2. Read [`references/runtime.md`](references/runtime.md); its Directory, Font, and Dependency contracts are mandatory for every route.
3. Read [`workflows/routing.md`](workflows/routing.md).
4. Select exactly one top-level route and its active profile from the routing authority.
5. Read only the resulting runtime authority and its explicitly triggered supporting documents.

| Selected route / profile | Runtime authority |
|---|---|
| Generate PPTX — Beautify | [`workflows/profiles/beautify-pptx.md`](workflows/profiles/beautify-pptx.md); explicit Quick intent selects Quick, otherwise Default |
| Generate PPTX — ordinary Default | [`workflows/generate-pptx.md`](workflows/generate-pptx.md) |
| Generate PPTX — ordinary explicit Quick | [`workflows/profiles/quick-generate.md`](workflows/profiles/quick-generate.md) |
| Create Template | [`workflows/create-template.md`](workflows/create-template.md) |
| Fill Native PPTX | [`workflows/template-fill-pptx.md`](workflows/template-fill-pptx.md) |
| Enhance Native PPTX | [`workflows/native-enhance-pptx.md`](workflows/native-enhance-pptx.md) |

**Hard rule — selected authority only**: Do not load another top-level route's
procedure after routing. Beautify selects exactly one Generate runtime from the
explicit Quick signal; never load both Default and Quick. Profiles, stages,
governance files, and child workflows refine one selected route; they never
compete with it.

---

## Global Execution Discipline

1. **Serial execution** — Follow the selected authority's steps in order. A completed non-blocking step may continue directly to the next eligible step.
2. **Blocking means stop** — At every `⛔ BLOCKING` gate, wait for explicit user confirmation. Do not decide on the user's behalf.
3. **No cross-phase bundling** — Do not combine work across an unclosed gate. Once the route's final user gate closes, later non-blocking steps may continue automatically.
4. **Gate before entry** — Verify every listed prerequisite before entering a step.
5. **No speculative execution** — Do not prepare later-phase artifacts before their owning step.
6. **Deterministic routing** — Do not add a route-choice question when [`routing.md`](workflows/routing.md) resolves the request. If a route prerequisite is missing, state it and stop that route.
7. **Owning-source recovery** — On failure, repair or regenerate the owning source artifact and resume from the route's declared pointer. Do not silently downgrade a required artifact.
8. **Stable paths** — Use absolute skill/project paths; never derive them from CWD.

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
