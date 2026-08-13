<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Step 6: Generate Image`

### Step 6: Generate Image

1. Resolve the backend per the `## Image Generation Tools` rule at the top of this file.
2. Ensure the full final prompt is persisted at `prompts/infographic.md` (already written in Step 5) BEFORE invoking the backend — the file is the reproducibility record.
3. **Check for existing file**: Before generating, check if `infographic.png` exists
   - If exists: Rename to `infographic-backup-YYYYMMDD-HHMMSS.png`
4. Call the chosen backend with the prompt file and output path.
   - **`codex-imagegen` invocation**: when the rule resolves to `codex-imagegen`, see [references/codex-imagegen.md](../../upstream/references/codex-imagegen.md) for the invocation contract (preferred `baoyu-image-gen --provider codex-cli` path, runtime wrapper discovery, parameter notes, stdout schema, batch semantics).
5. On failure, auto-retry once

Text correction policy:

- If labels, headings, callouts, data values, or any other rendered text is misspelled, garbled, hard to read, or visually weak, do not patch the bitmap with code.
- For text-correction regenerations, write a new prompt file and a new output path so the flawed candidate is preserved for comparison.
- Post-processing is limited to crop, resize, compression, or format conversion that does not alter text or the main composition.
