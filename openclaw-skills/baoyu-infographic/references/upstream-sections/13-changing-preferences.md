<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Changing Preferences`

## Changing Preferences

EXTEND.md lives at the first matching path in Step 1.1. Edit it directly (schema: `references/config/preferences-schema.md`), or delete it / ask "reconfigure baoyu-infographic preferences" / "重新配置" to re-run first-time setup. Common edits:

- `preferred_image_backend`: `auto` (default; runtime-native wins, else the only installed backend, ask if multiple non-native) | `codex-imagegen` | `baoyu-image-gen` | `ask` (confirm every run)
- `preferred_layout: dense-modules`, `preferred_style: morandi-journal`, `preferred_aspect: portrait`, `language: zh` — shift Step-3 recommendations and Step-4 defaults (never bypass Step 4).
