<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Reference Images`

## Reference Images

Users may supply refs via `--ref <files...>`, file paths, or pasted images; they guide style, palette, composition, or subject. Step 1.0 in [references/workflow.md](../../upstream/references/workflow.md) saves them to `references/NN-ref-{slug}.{ext}`; Step 5.3 processes per-illustration usage `direct | style | palette`. When the backend supports batch input, propagate `direct` entries from each prompt file's `references:` frontmatter into its batch task (e.g. `baoyu-image-gen` accepts `ref` per task).
