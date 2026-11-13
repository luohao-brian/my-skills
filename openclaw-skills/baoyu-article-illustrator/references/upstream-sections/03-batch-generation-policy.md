<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Batch Generation Policy`

## Batch Generation Policy

After every prompt file for the run has been saved and verified, generate images in batches by default:

1. Use the chosen backend's native batch / multi-task interface if it exists. Each task keeps its own prompt file, output path, aspect ratio, and direct reference images.
2. Otherwise, if the runtime can issue parallel tool calls, dispatch up to `generation_batch_size` images at a time (default `4`). An explicit request in the current message (`--batch-size 4`, "并行4张一起生成") overrides EXTEND.md.
3. Otherwise generate sequentially.

- Never start a batch until all its prompt files exist on disk.
- Retry failed items once without regenerating successful ones.
- Don't use subagents just to parallelize rendering; only for separate per-image prompt iteration or creative exploration.
