<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Step 6: Generate Image`

### Step 6: Generate Image

1. Resolve the backend per `## Image Generation Tools`.
2. Ensure the full final prompt is persisted at `prompts/infographic.md` (Step 5) BEFORE invoking the backend.
3. If `infographic.png` exists, rename to `infographic-backup-YYYYMMDD-HHMMSS.png`.
4. Call the backend with the prompt file and output path. For `codex-imagegen`, see [references/codex-imagegen.md](../../upstream/references/codex-imagegen.md).
5. On failure, auto-retry once.

Text correction: never patch misspelled, garbled, or weak rendered text (labels, headings, callouts, data values) in the bitmap with code. Write a new prompt file and a new output path so the flawed candidate is kept for comparison. Post-processing is limited to crop, resize, compression, or format conversion that doesn't alter text or composition.
