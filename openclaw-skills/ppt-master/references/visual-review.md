# Visual Review Rubric

> Per-page visual self-check rubric for slide SVGs. It may be executed serially, concurrently, or through delegation according to the calling runtime. Companion to the [`visual-review` stage](../workflows/stages/visual-review.md) and the [`visual_review.py`](../scripts/visual_review.py) renderer.

## §0 Prerequisites

This rubric **does not repeat** what `svg_quality_checker.py` already covers. Required upstream order:

```
Executor finishes page → svg_quality_checker.py passes → visual_review.py renders PNG → this rubric runs
```

If the static checker has not been run or has failed, the review must abort with status `prereq_failed` and not start the rubric. Topics already enforced by the static checker (do **not** re-check here):

- font-size anchor drift (more than `2px` from every declared role anchor)
- id uniqueness, XML well-formed
- canvas/structural typography validation and informational spec-lock anchor comparison (contextual colors/fonts are allowed)
- animation_config compliance

## §0.1 Review inputs

Each review work unit processes a **batch** of pages (see §6.1 for batch sizing). The inputs are:

1. **Page batch** — a list of `(svg_path, png_path, page_role)` tuples, one per assigned page. `svg_path` resolves under `<project>/svg_output/<page>.svg`, `png_path` under `<project>/.preview/<page>.png`. `page_role` is one of `cover` / `chapter` / `tldr` / `content` / `data` / `closing` / `breathing`, parsed from `design_spec.md §IX` before review; reviewers do **not** guess.
2. **Path to this rubric file**
3. **`<project>/design_spec.md`** (read-only) — §IX outline is the source of truth for "what should this page deliver"
4. **`<project>/spec_lock.md`** (read-only) — brand-locked values
5. **`<project>/.review/`** (writable) — where backups and findings JSON go

The review executor reads inputs 2–4 **once** before processing its batch, then iterates over the pages sequentially: apply the rubric → write `<project>/.review/<page>.json` → move on. Reusing the shared inputs is an optimization, not a requirement for any particular task or Agent API.

## §1 Hard rules (fix every hit)

| # | Category | Trigger | Permitted fix |
|---|----------|---------|---------------|
| H1 | Out-of-bounds | element bbox falls outside `0,0,1280,720` | shrink or reposition into canvas |
| H2 | Text overflow | text bbox extends past its visual container | reduce font-size or line-break |
| H3 | Text overlap | two `<text>` elements' bboxes intersect (tspans within one text excluded) | reposition or resize |
| H4 | Readability | contrast < 4.5 (small text) / < 3.0 (font-size ≥ 24px); OR text directly atop a complex image with no scrim | if **neither** the foreground nor the background color is a brand token: position-only escape — add a `<rect>` scrim under the text, or raise the offending text's font-size to ≥ 24px so the 3.0 threshold applies. If **either** color is a brand token: do not edit the SVG → goto §1.1 escalation. |
| ~~H5~~ | Font-ramp drift | *covered by `svg_quality_checker.py` — see §0 prerequisites* | n/a (do not re-check) |
| H6 | Element collision | rect/circle/path bboxes overlap with z-order violating semantics | open spacing |
| H7 | Anchored element displaced | page number / header / footer covered, missing, or out of canvas | restore to anchor position |
| H8 | Image rendering broken | `<image>` empty / broken-image / severe distortion | fix `href`; for `adaptive`, choose `meet` or a safer crop; a new complete-display requirement returns to §VIII `Crop Policy` and lock projection |
| H9 | Missing key element | element required by `design_spec §IX` outline is absent from rendered slide | recreate from spec |

Detection order (run sequentially within one page review):

```
H1 → H2 → H7  (structure)
H3 → H6      (collisions)
H4           (readability)
H8 → H9      (content)
```

### §1.1 Brand-token contrast escalation

If H4 fires and the foreground or background color is a **brand token** (defined in `spec_lock.md`) — i.e., the violation will repeat on every page using that token — do **not** touch the SVG. Brand decisions are §3 Don't-Touch; even position-only escapes (scrim insertion, font-size escalation) shift the page's visual weight in ways that should be a brand-level decision, not a per-page review decision. Instead:

1. Record the finding in the page JSON under `needs_human_items` with `rule: "H4"`, the offending element selector, and `suggested_fix_summary` describing the brand-level options (e.g., "raise body-text token from `#6E7681` to `#8B949E` deck-wide" or "introduce a scrim style in the brand").
2. Append the finding to `<project>/.review/brand_review.json` (append-only log; one entry per distinct token+context pair). Aggregate and surface this file at the end so the user can make one cross-deck decision instead of N per-page ones.
3. The page's `status` is `needs_human` if H4 is the only Hard hit on the page; if other (non-brand) Hard hits were fixed, the page still finishes as `fixed` and the brand-token H4 entry sits in `needs_human_items` alongside.

The aggregate step owns the brand review; an individual page review does not.

## §2 Soft rules (act only when clearly bad)

Subagents must apply the **明显** ("clearly bad") threshold — when in doubt, leave it. Better to under-fix than to oscillate.

| # | Category | Trigger | Fix direction |
|---|----------|---------|---------------|
| S1 | Vertical rhythm tight | Within the **same logical text block**, consecutive baselines have gap < 1.05× larger font-size | open to 1.15–1.3× |
| S2 | Vertical rhythm hollow | Within one logical block, > 150 px non-decorative whitespace; `breathing` pages exempt | tighten |
| S3 | Visual centroid off | hero/title block centroid offset from canvas center exceeds threshold by `page_role`: `cover` > 35%, `chapter` > 25%, `tldr`/`closing`/`breathing` > 25%, `content`/`data` > 20% | shift toward intended anchor |
| S4 | Alignment drift | same-column elements differ in `x` by > 4 px (or same-row baselines by > 4 px) **and** are semantically meant to be on the same grid line | snap to grid |
| S5 | Grid non-uniform | N-card row: neighbor `x`-spacing differs by > 5% of the average | re-distribute |
| S6 | CJK letter-spacing | CJK characters with `letter-spacing / font-size > 5%` | reduce to ≤ 2% |
| S7 | Accent overload | > 2 accent colors across ≥ 3 distinct elements | collapse to 1 primary + 1 secondary |
| S8 | Emphasis mismatch | most visually prominent element ≠ the element `design_spec §IX` declares as the page's primary | rescale to match intent |
| S9 | Image-text relationship | caption > 60 px from its image; text on busy image without scrim; image clearly purposeless | tighten / add scrim / remove |
| S10 | Breathing violation | only when `page_role = breathing`: ≥3 rounded card grid | replace with naked text / single hero |

## §3 Don't-touch

Hard boundary, equal weight to §1.

- **Brand decisions** — color tokens, font families, geometry style (decided by `spec_lock.md` / brand directory)
- **Layout restructure** — do not change column counts, replace chart types, add/remove sections
- **Content** — do not add or remove copy; only adjust position, font-size (within the mapped role's anchor `±2px`), spacing, letter-spacing, alignment, scrim
- **Other files** — never edit `design_spec.md` / `spec_lock.md` / `animations.json` / `image_prompts.json` / `images/` / other pages' SVGs
- **Atomicity** — one edit per fix, no bulk multi-element replacements

If a "violation" requires reinterpreting `design_spec.md` to fix → mark `needs_human` with a one-line `suggested_fix_summary`.

## §4 Iteration protocol

### §4.0 Iteration 0 — PNG sanity check

Run before applying any rule:

- PNG file exists and is non-zero bytes
- PNG dimensions = 1280 × 720
- PNG is **not** all-background (a histogram check: count of background-color pixels < 99% of total) — guards against blank/white-out renders only, **does not** filter sparse dark layouts

Any check fails → status = `render_failed`, abort without scanning rules.

### §4.1 Iteration loop

The full loop is defined here but the **default budget is 1 iteration**. Multi-iteration runs require explicit opt-in in the selected execution plan and roughly double render cost per added iteration.

```
iteration 1: scan all Hard + Soft → fix → (re-render only if budget ≥ 2)
iteration 2 (opt-in): re-verify changed elements + scan for new Hard hits → fix → re-render
iteration 3 (opt-in): report only, no further fix
```

Per-iteration fix caps:

- **Hard rules**: no per-round cap — every Hard hit must be addressed in the iteration it was found in
- **Soft rules**: ≤ 2 fixes per iteration; remaining Soft hits go to `untouched_concerns`

### §4.2 Termination conditions

- **Rollback trigger**: any iteration's fix introduces a **new Hard hit** that did not exist before → immediately `cp` the backup back over the SVG, status = `needs_human`, finding records "rolled back fix X — created Hard Y"
- **Soft thrash trigger** (iteration budget ≥ 2 only): iteration 2's fix introduces a **new Soft hit** that did not exist before → stop, status = `needs_human` with note "fixes are competing"
- **Clean exit**: iteration ends with zero Hard hits and ≤ 1 Soft hit remaining → status = `ok` if no fixes were applied, `fixed` if any were applied

### §4.3 Backup discipline

Before the **first** edit on a page in any iteration `N`, the review executor must:

```bash
cp <project>/svg_output/<page>.svg <project>/.review/backup/<page>.iter<N>.svg
```

The backup path is recorded in every finding's `backup_path` field. Backups are the rollback anchor for §4.2.

## §5 Output schema

Each page review writes exactly one file to `<project>/.review/<page>.json`:

```json
{
  "page": "02_three_steps.svg",
  "page_role": "content",
  "status": "ok" | "fixed" | "needs_human" | "render_failed" | "prereq_failed",
  "iterations_run": 1,
  "screenshot_paths": [
    ".preview/02_three_steps.png",
    ".preview/02_three_steps.iter1.png"
  ],
  "findings": [
    {
      "iter": 1,
      "rule": "S6",
      "severity": "soft",
      "evidence": "letter-spacing=10 on font-size=84, ratio=11.9% > 5%",
      "fix_applied": {
        "element": "#hero-statement text[font-size='84']",
        "before": "letter-spacing=\"10\"",
        "after": "letter-spacing=\"2\""
      },
      "verified_in_iter": 2,
      "backup_path": ".review/backup/02_three_steps.iter1.svg"
    }
  ],
  "untouched_concerns": [
    {
      "rule": "S1",
      "evidence": "...",
      "reason": "soft-cap reached" | "ambiguous_design_intent"
    }
  ],
  "needs_human_items": [
    {
      "rule": "H9",
      "suggested_fix_summary": "Hero subtitle declared in spec §IX.4 missing; add a <text> at (80,496) per design language"
    }
  ],
  "design_intent_check": {
    "spec_says": "TL;DR — emphasize 意图 as the core abstraction",
    "render_delivers": true,
    "note": "..."
  }
}
```

`needs_human_items` must include a `suggested_fix_summary` for every entry — never bare problem descriptions.

## §6 Execution and batching contract

This rubric defines page-review inputs and outputs. The calling runtime chooses
whether one executor handles all pages, batches run serially, compatible work is
parallelized, or review is delegated. No team API, worker type, prompt transport,
messaging primitive, or named role is required.

### §6.1 Batches

Partition N pages into batches of at most K pages (default **K = 5**) when doing
so reduces repeated reads of the rubric, `design_spec.md`, and `spec_lock.md`.
A single executor may instead process the full deck when that better fits its
context and capabilities.

Every batch must be self-contained: provide the §0.1 inputs, the full
`(svg_path, png_path, page_role)` list, and the forbid list. Do not rely on prior
conversation state. If work is delegated, the caller maps this contract to its
actual task interface; PPT Master does not prescribe that interface.

**Batch size guidance**:
- `K = 5` (default) — balanced for typical decks
- `K = 3` — high-fidelity review of a short deck
- `K = 10` — fewer repeated shared-input reads for a large deck

Keep K within the selected executor's context budget. Batch sizing is an
optimization, not a correctness or parallelism requirement.

### §6.2 Completion and aggregation

- Write one page JSON for every attempted page, including aborted pages marked
  `needs_human` or `render_failed`.
- Aggregate those files into the page-status Markdown table and include the path
  to `brand_review.json` when present.
- Use the calling runtime's normal return or reporting mechanism. Do not require
  a specific send-message API or idle-state protocol.

### §6.3 Concurrency

Pre-rendering is serialized by `visual_review.py`'s file lock at
`<project>/.preview/.render.lock`. Re-renders during the iteration loop use the
same lock. Other work may run concurrently only when it does not edit the same
page or shared review file.

## §7 Renderer expectations *(script contract)*

`visual_review.py <project> [pages...]` must guarantee:

- Output PNG matches what the user would see in the live-preview browser (inlined `<use data-icon>`, resolved `<image href>`)
- Output dimensions = 1280 × 720
- File-lock serialization at `<project>/.preview/.render.lock`
- Clean exit codes:
  - `0` — all requested pages rendered
  - `2` — live-preview server not running for this project (do not retry blindly; surface to the caller)
  - `3` — rendering backend (playwright + chromium) missing or unable to launch (config error, surface to user)
  - `4` — page-level render failure (specific failures listed in stderr; partial output is acceptable)

The renderer never edits SVGs and never reads any rule from this rubric — it is a pure render-and-validate tool.
