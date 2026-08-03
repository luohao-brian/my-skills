---
description: Optional quality-gate stage for per-page rubric-based visual review.
---

# Visual Review Stage

> Optional Generate-PPTX quality stage. Goal: reduce human iteration by applying a fixed visual rubric to each rendered slide and making atomic position/spacing fixes.
>
> Reads `<project>/svg_output/<page>.svg` and a pre-rendered PNG of each slide, then either applies a fix or flags `needs_human`. **Never touches** brand decisions, layout structure, or other files.
>
> This stage is **context-independent** — invokable in a fresh chat session with only `<project_path>` as input. No upstream conversation context required.

## Positioning

This is an **optional auxiliary loop**, opt-in only. The [`generate-pptx`](../generate-pptx.md) Step 1–7 pipeline does not invoke it; trigger only when the user explicitly asks for a visual re-pass on the generated SVGs before export.

**Cost note**: visual inspection can be expensive. Process several pages after reading the shared rubric, `design_spec.md`, and `spec_lock.md` once. The calling runtime decides whether that work runs serially, concurrently, or through delegation.

## When to Run

- Executor ([`generate-pptx`](../generate-pptx.md) Step 6) has finished all pages
- `svg_quality_checker.py` has passed
- Post-processing (`finalize_svg.py`, `svg_to_pptx.py`) has **not** yet run
- The user has explicitly requested visual review

For decks containing data charts, run [`verify-charts`](./verify-charts.md) first — visual-review focuses on visual rhythm / collision / alignment, not chart coordinate math.

## When NOT to Run

- The project has no `svg_output/<page>.svg` files yet — finish Executor first
- `svg_quality_checker.py` has not been run or has failed — fix static violations first
- User has already applied annotations via the `live-preview` stage and is in a fixed-edit loop — describe changes directly, do not re-trigger rubric
- The user has not asked for it — do not auto-invoke based on inferred model capability or deck size

---

## Prerequisites

The caller's selected Python environment must already expose Playwright and a
compatible browser, or the runtime must expose an equivalent screenshot
capability. Do not install packages, create an environment, or download a
browser from this stage. If no renderer is available, report the skipped visual
review.

Start the project-local live-preview server when using `visual_review.py`:

```bash
python3 {baseDir}/scripts/svg_editor/server.py <project_path> --no-browser
# (single instance per project — if it's already running, skip)
```

The renderer (`visual_review.py`) does **not** auto-start the live-preview server. Without `--server-url`, it discovers the actual port from the target project's `live_preview/lock.json`; an explicit `--server-url` overrides discovery. In either case it validates `/api/health` against the resolved target project before rendering and rejects a server for another project.

> **Why playwright, not cairosvg**: cairo's text API has no font-fallback chain, so CJK characters render as tofu boxes for a deck that relies on system fallback. Playwright drives a real chromium and produces output identical to what the live-preview browser shows. This validates authored SVG appearance only; it never proves that the first PowerPoint face is installed or that the exported PPTX is portable. Step 7.5 must still render the actual PPTX.

---

## Step 1 — Pre-render all PNGs

```bash
python3 {baseDir}/scripts/visual_review.py <project_path>
```

This writes one PNG per page to `<project_path>/.preview/<page>.png` at 1280×720, with `<use data-icon>` inlined and `<image href>` resolved exactly as the live-preview browser sees them. Renders are serialized via a project-local file lock — safe to invoke concurrently.

Exit codes:

- `0` — all pages rendered
- `2` — live-preview server unreachable or serving a different project (start the target project's server per Prerequisites)
- `3` — Playwright or a compatible Chromium runtime is unavailable (or browser launch failed)
- `4` — one or more page-level render failures (see stderr; partial output is on disk)

If any page comes back with `"all_background": true` in the JSON summary, that page rendered to a blank surface — investigate before continuing (broken `<use>` reference, missing image asset, etc.).

---

## Step 2 — Review page batches

Partition the N pages into batches of at most K pages (default **K = 5**). The
calling runtime owns execution strategy: the current executor may process every
batch serially, use compatible parallel work primitives, or delegate when such
capability is available. PPT Master does not require a team API, worker type,
message primitive, or named role.

Every review work unit must be self-contained and include:

- `<project_path>` — project root
- Full page list with `page_role` per page (parse `<project>/design_spec.md` §IX outline; **fixed compatibility default**: if an existing `design_spec.md` lacks §IX, use `content` for every page and flag this in the final report; if `design_spec.md` itself is missing, restore it through [`failure-recovery.md`](../governance/failure-recovery.md) §3 before dispatch)
- Batch size `K` (default 5; raise to 10 for token-sensitive runs on large decks, lower to 3 for high-fidelity short decks — see rubric §6.1)
- Iteration budget per page (default 1; 2 only for high-stakes / final-cut runs — see [Appendix: Iteration loop](#appendix-iteration-loop-opt-in))
- Path to the rubric: `{baseDir}/references/visual-review.md`
- Execution contract reference: rubric [§6](../../references/visual-review.md#6-execution-and-batching-contract)
- Forbid list: do not edit any other page, `design_spec.md`, `spec_lock.md`, `animations.json`, `image_prompts.json`, or `images/`

---

## Step 3 — Aggregate findings

Aggregate the per-page JSON files into this Markdown table:

```
| page | role | status | hard_hits | soft_hits | fixes_applied | needs_human_reason |
|------|------|--------|-----------|-----------|---------------|---------------------|
```

Statuses:

- `ok` — page passed clean, no fixes applied
- `fixed` — at least one fix applied, all Hard rules now pass
- `needs_human` — fix attempted but rolled back (rule §4.2), or rule violation requires brand/structure decision outside the rubric's scope
- `render_failed` — Iteration 0 PNG sanity failed (rare; usually means renderer / server issue)
- `prereq_failed` — static checker hadn't been run

Plus a brand-token aggregate at `<project>/.review/brand_review.json` if any §1.1 escalations occurred — review this once at the end of the run, not per page.

---

## Step 4 — Decide next move

For each row in the table:

- `ok` / `fixed` — no action; the SVG has been updated in-place (originals are at `<project>/.review/backup/<page>.iter<N>.svg`)
- `needs_human` — read the page's JSON `needs_human_items[].suggested_fix_summary`, decide with the user whether to apply or defer
- `render_failed` — re-run `visual_review.py` for that page only (`--pages <token>`); if it persists, hand off to manual review
- `prereq_failed` — go back and run `svg_quality_checker.py`

If `brand_review.json` is non-empty, that's a single decision applied across the deck (e.g., bump footer text color from `#6E7681` to `#8B949E` — one change, every page benefits). Do this once, then optionally re-run visual-review for the affected pages only.

After the table is clean, continue to [`generate-pptx`](../generate-pptx.md)
Step 7. That authority owns the serial commands, gates, and success criteria for
post-processing and export.

---

## Notes & invariants

- **Single source of truth for rules**: [`references/visual-review.md`](../../references/visual-review.md). This stage file is just the orchestration — never restate or paraphrase rules here.
- **Concurrency**: `visual_review.py` serializes renders via `<project>/.preview/.render.lock`. Every caller uses that renderer or an equivalent runtime-owned serialization mechanism.
- **Iteration budget**: default 1 iteration. Bumping to 2 doubles render cost and roughly triples token cost. Only worth it for high-stakes / final-cut decks.
- **Don't-touch (rubric §3)** applies to every review executor. Brand-color changes are out of scope; make them through the owning design workflow, then re-render and review again.
- **Backups**: every modified SVG has a `.review/backup/<page>.iter<N>.svg` rollback anchor. Restore by `cp`.
- **The rubric is not the designer**: it catches collisions, drift, and rhythm errors — it does not improve a fundamentally weak layout. If 80%+ of pages come back `needs_human`, the Design Spec's pattern selection or Executor's realization geometry is the root cause, not this stage.
- **Screenshot output discipline**: direct browser/screenshot capabilities may resolve relative paths from their own working directory. Request an explicit path under `<project_path>/.preview/` for project artifacts or use the caller's managed temporary directory for one-off probes. Never write probes into the Skill source or repository.

---

## Appendix: Iteration loop (opt-in)

Default behavior is single-iteration review: one scan, fix in place, write the report. The full iteration loop in [`references/visual-review.md`](../../references/visual-review.md) §4.1 supports:

1. Iteration 1: scan + fix
2. Re-render via `visual_review.py --pages <token>`
3. Iteration 2: re-verify changed elements + scan for new Hard hits
4. Rollback on any new Hard hit introduced by a fix

To enable, set the selected review execution's iteration budget to 2; `visual_review.py` does not enforce this policy. Each added iteration roughly doubles render cost and triples token cost on the affected pages — reserve for final-cut runs only.
