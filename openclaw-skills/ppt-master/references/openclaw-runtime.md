# OpenClaw Runtime Contract

## Upstream baseline and overlay

- Repository: `https://github.com/hugohe3/ppt-master`
- Imported core commit: `6b42a6a652f9d6e9fc0c81e634c9fdfe771eee10` (2026-07-31)
- The OpenClaw overlay retains single-line metadata, `{baseDir}` resolution, external project roots, runtime-neutral media, and deterministic SVG/PPTX release checks.
- The later upstream independent-identity guard is intentionally not imported because it rejects the OpenClaw metadata and runtime adapter contract. See [`upstream-source.md`](upstream-source.md).

## Dependencies

Install into an external environment, never into the skill directory:

```bash
uv venv <external-cache>/ppt-master-venv
uv pip install --python <external-cache>/ppt-master-venv/bin/python \
  -r {baseDir}/requirements.txt
<external-cache>/ppt-master-venv/bin/python -m playwright install chromium
```

The browser audit may use installed Chrome when Playwright-managed Chromium is unavailable.

Resolve the Python executable once after dependency setup and reuse that exact
executable for every PPT Master command. Do not assume an activated virtual
environment or a modified `PATH` survives across Agent tool calls. Before
starting work, use the resolved interpreter to import the dependencies needed
by the selected route (including Pillow for raster images and Playwright for
the browser audit); a failed import is an environment failure, not a corrupt
project asset. The command examples below use `python3` as a placeholder for
that resolved executable.

## External project root

Resolve an absolute project root before initialization. Prefer the user-selected output directory; otherwise use a dedicated directory inside the current runtime workspace. Never use `{baseDir}/projects`, a relative `projects/`, or a source-repository directory.

```bash
PROJECTS_ROOT="<absolute runtime-workspace directory>"
python3 {baseDir}/scripts/project_manager.py init <name> --format ppt169 --dir "$PROJECTS_ROOT"
```

Pass the resulting absolute project path to every subsequent command.

## Runtime media

Read [`runtime-media.md`](runtime-media.md) before AI image or narration work. Discover the current Agent's available tools/skills and adapt to their declared schemas. The workflow may request an image or TTS capability, but must not bind itself to an Agent, provider, model, key, or one fixed parameter spelling.

## Release gate

Run against authored `svg_output/` before export:

```bash
python3 {baseDir}/scripts/project_manager.py validate <absolute-project>
python3 {baseDir}/scripts/svg_quality_checker.py <absolute-project>
python3 {baseDir}/scripts/visual_layout_audit.py <absolute-project>
```

The static checker owns source-contract violations. The browser audit owns rendered bounds and derives four viewport equivalence classes from the SVG canvas: native, fractional same-aspect, wider, and taller. It waits for fonts and image resources before measuring.

- Objective failures block: invalid/non-positive rendered geometry, broken resources, or visible content outside the SVG canvas.
- Heuristics are advisory: likely collisions, container overflow, low utilization, and edge crowding. Fix, explain as intentional, or record a release note.
- Repeating the same element issue across viewports is one issue with occurrence details, not four independent failures.

After export, validate the actual package and DrawingML geometry:

```bash
python3 {baseDir}/scripts/pptx_delivery_check.py <absolute-pptx>
python3 {baseDir}/scripts/pptx_layout_audit.py <absolute-pptx>
```

The delivery checker owns package integrity and release blockers. The layout audit catches shapes outside slides and degenerate geometry; text-frame overlap, utilization, and edge crowding are advisory because intentional overlays are common. Group children are measured in slide coordinates, including nested scale/offset transforms. A horizontal or vertical connector is valid when only one dimension is zero.

When an export-side issue traces to SVG geometry, repair `svg_output/`, rerun the pre-export checks, and export again. Do not edit the package merely to hide the source defect.

## Visual review

Deterministic checks cannot judge narrative hierarchy, contrast, image meaning, template fit, or overall polish. Render the final deck and inspect a montage after package checks; use [`../workflows/stages/visual-review.md`](../workflows/stages/visual-review.md) when its route trigger applies.

## Failure reporting

Report the exact command/exit code, affected page and element when available, whether the finding is blocking or advisory, artifacts not produced, and the recovery action taken.
