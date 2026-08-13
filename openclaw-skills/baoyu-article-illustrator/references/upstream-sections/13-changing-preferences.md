<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Changing Preferences`

## Changing Preferences

EXTEND.md lives at the first matching path listed in Step 1.5. Three ways to change it:

- **Edit directly** — open EXTEND.md and change fields. Full schema: `references/config/preferences-schema.md`.
- **Reconfigure interactively** — delete EXTEND.md (or ask "reconfigure baoyu-article-illustrator preferences" / "重新配置"). The next run re-triggers first-time setup.
- **Common one-line edits**:
  - `preferred_image_backend: auto` — default; runtime-native tool wins, falls back to the only installed backend, asks only if multiple non-native are present.
  - `preferred_image_backend: codex-imagegen` — pin to Codex's built-in.
  - `preferred_image_backend: baoyu-image-gen` — pin to the baoyu-image-gen skill.
  - `preferred_image_backend: ask` — confirm backend every run.
  - `generation_batch_size: 4` — default number of images to render concurrently when the runtime supports parallel generation calls.
  - `preferred_type: infographic`, `preferred_style: notion`, `preferred_palette: macaron`, `language: zh`.
  - `default_output_dir: imgs-subdir` — where to write generated images relative to the article.
