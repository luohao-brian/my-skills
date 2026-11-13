<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Changing Preferences`

## Changing Preferences

EXTEND.md lives at the first matching path in Step 1.5. Edit it directly (schema: [references/config/preferences-schema.md](../../upstream/references/config/preferences-schema.md)), or delete it / ask "reconfigure baoyu-article-illustrator preferences" / "重新配置" to re-run first-time setup. Common edits:

- `preferred_image_backend`: `auto` (default; runtime-native wins, else the only installed backend, ask if multiple non-native) | `codex-imagegen` | `baoyu-image-gen` | `ask` (confirm every run)
- `generation_batch_size: 4` — concurrent renders when parallel calls are supported
- `preferred_type: infographic`, `preferred_style: notion`, `preferred_palette: macaron`, `language: zh`
- `default_output_dir: imgs-subdir`
