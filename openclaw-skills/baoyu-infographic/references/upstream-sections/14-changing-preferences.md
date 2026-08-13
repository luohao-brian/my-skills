<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Changing Preferences`

## Changing Preferences

EXTEND.md lives at the first matching path in Step 1.1. Three ways to change it:

- **Edit directly** — open EXTEND.md and change fields. Full schema: `references/config/preferences-schema.md`.
- **Reconfigure interactively** — delete EXTEND.md (or ask "reconfigure baoyu-infographic preferences" / "重新配置"). The next run re-triggers first-time setup.
- **Common one-line edits**:
  - `preferred_image_backend: auto` — default; runtime-native tool wins, falls back to the only installed backend, asks only if multiple non-native are present.
  - `preferred_image_backend: codex-imagegen` — pin to Codex's built-in.
  - `preferred_image_backend: baoyu-image-gen` — pin to the baoyu-image-gen skill.
  - `preferred_image_backend: ask` — confirm backend every run.
  - `preferred_layout: dense-modules`, `preferred_style: morandi-journal`, `preferred_aspect: portrait`, `language: zh` — shift the Step-3 recommendations and Step-4 defaults (per [Confirmation Policy](#confirmation-policy), these never bypass Step 4).
