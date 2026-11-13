<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Step 1: Setup & Analyze`

### Step 1: Setup & Analyze

**1.1 Load Preferences (EXTEND.md)** — first match wins:

| Priority | Path | Scope |
|----------|------|-------|
| 1 | `.baoyu-skills/baoyu-infographic/EXTEND.md` | Project |
| 2 | `${XDG_CONFIG_HOME:-$HOME/.config}/baoyu-skills/baoyu-infographic/EXTEND.md` | XDG |
| 3 | `$HOME/.baoyu-skills/baoyu-infographic/EXTEND.md` | User home |

Found → read, parse, display a one-line summary. Not found → ask the user with `AskUserQuestion` per `references/config/first-time-setup.md`. Supports preferred layout/style, default aspect, language, image backend, custom styles (schema: `references/config/preferences-schema.md`).

**1.2 Analyze Content → `analysis.md`** (format: `references/analysis-framework.md`)

1. Save source content (file path or paste → `source.md`). **Backup rule**: if `source.md` exists, rename to `source-backup-YYYYMMDD-HHMMSS.md`
2. Analyze: topic, data type, complexity, tone, audience
3. Detect source language and user language
4. Extract design instructions from user input
5. Save analysis. **Backup rule**: if `analysis.md` exists, rename to `analysis-backup-YYYYMMDD-HHMMSS.md`
