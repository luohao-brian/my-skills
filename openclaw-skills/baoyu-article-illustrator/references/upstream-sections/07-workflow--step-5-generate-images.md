<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Step 5: Generate Images`

### Step 5: Generate Images

⛔ **Prompt files MUST be saved before ANY image generation**, whatever the backend.

1. Per illustration, write `prompts/NN-{type}-{slug}.md` (YAML frontmatter) per [references/prompt-construction.md](../../upstream/references/prompt-construction.md): type-specific template with ZONES / LABELS / COLORS / STYLE / ASPECT; LABELS use article-specific data (actual numbers, terms, metrics, quotes). Never pass ad-hoc inline prompts to `--prompt` without saving prompt files first.
2. Select the backend once per session via `## Image Generation Tools`. For `codex-imagegen`, see [references/codex-imagegen.md](../../upstream/references/codex-imagegen.md).
3. Process references (`direct`/`style`/`palette`) per prompt frontmatter; apply watermark if EXTEND.md enables it.
4. Generate from saved prompt files per `## Batch Generation Policy`; retry once on failure.

See [workflow.md](../../upstream/references/workflow.md#step-5-generate-images).
