<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Batch Generation Policy`

## Batch Generation Policy

After every prompt file for the run has been saved and verified, generate images in batches by default.

Priority order:

1. Use the chosen backend's native batch / multi-task interface if it exists. Each task must keep its own prompt file, output path, aspect ratio, and direct reference images.
2. If no native batch interface exists but the runtime can issue parallel tool calls, dispatch up to `generation_batch_size` images at a time. Default: `4`. An explicit user request in the current message, such as `--batch-size 4` or "并行4张一起生成", overrides EXTEND.md.
3. If neither native batch nor parallel tool calls are available, generate sequentially.

Rules:

- Never start the first batch until all prompt files for that batch exist on disk.
- Retry failed items once without regenerating successful items.
- Do not use subagents merely to parallelize image rendering. Use subagents only for separate prompt iteration or creative exploration.
