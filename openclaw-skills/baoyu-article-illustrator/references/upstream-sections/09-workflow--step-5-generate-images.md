<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Step 5: Generate Images`

### Step 5: Generate Images

⛔ **BLOCKING: Prompt files MUST be saved before ANY image generation.** This is a hard requirement regardless of which backend is chosen — the prompt file is the reproducibility record.

1. For each illustration, create a prompt file per [references/prompt-construction.md](../../upstream/references/prompt-construction.md)
2. Save to `prompts/NN-{type}-{slug}.md` with YAML frontmatter
3. Prompts **MUST** use type-specific templates with structured sections (ZONES / LABELS / COLORS / STYLE / ASPECT)
4. LABELS **MUST** include article-specific data: actual numbers, terms, metrics, quotes
5. **DO NOT** pass ad-hoc inline prompts to `--prompt` without saving prompt files first
6. Select the backend via the `## Image Generation Tools` rule at the top: use whatever is available; if multiple, ask the user once. Do this once per session before any generation.
   - **`codex-imagegen` invocation**: when the rule resolves to `codex-imagegen`, see [references/codex-imagegen.md](../../upstream/references/codex-imagegen.md) for the invocation contract (preferred `baoyu-image-gen --provider codex-cli` path, runtime wrapper discovery, parameter notes, stdout schema, batch semantics).
7. **Execution strategy**: Generate in batches per the `## Batch Generation Policy`: backend native batch first, runtime parallel tool calls second, sequential only as fallback. Default batch size is 4 unless EXTEND.md or the current request overrides it.
8. Process references (`direct`/`style`/`palette`) per prompt frontmatter
9. Apply watermark if EXTEND.md enabled
10. Generate from saved prompt files; retry once on failure

Full procedures: [references/workflow.md](../../upstream/references/workflow.md#step-5-generate-images)
