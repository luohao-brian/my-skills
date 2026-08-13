<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Step 4: Confirm Options`

### Step 4: Confirm Options

**Hard gate**: this step is mandatory per the [Confirmation Policy](#confirmation-policy) — Steps 5–6 cannot start until the user confirms here (or explicitly opts out with `--no-confirm` / equivalent in the current request).

Ask the user to confirm the questions below following the [User Input Tools](#user-input-tools) rule at the top of this file (batch into one call if the runtime supports multiple questions; otherwise ask one at a time in priority order).

| Priority | Question | When | Options |
|----------|----------|------|---------|
| 1 | **Combination** | Always | 3+ layout×style combos with rationale |
| 2 | **Aspect** | Always | Named presets (landscape/portrait/square) or custom W:H ratio (e.g., 3:4, 4:3, 2.35:1) |
| 3 | **Language** | Only if source ≠ user language | Language for text content |
| 4 | **Image Backend** | Only if step 3 of the `## Image Generation Tools` rule needs to ask (no runtime-native tool AND multiple non-native backends, OR `preferred_image_backend: ask`) | Available backends |
