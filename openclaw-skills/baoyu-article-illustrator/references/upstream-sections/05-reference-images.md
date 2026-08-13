<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Reference Images`

## Reference Images

Users may supply reference images via `--ref <files...>` or by providing file paths / pasting images in conversation. Refs guide style, palette, composition, or subject for specific illustrations.

Full detection, storage, and processing rules are in [references/workflow.md](../../upstream/references/workflow.md) (Step 1.0 saves to `references/NN-ref-{slug}.{ext}`; Step 5.3 processes per-illustration usage `direct | style | palette`). When the chosen backend supports batch input, `direct`-usage entries in each prompt file's `references:` frontmatter should be propagated into its batch payload so backends can pass them through (e.g. `baoyu-image-gen` accepts `ref` per task).
