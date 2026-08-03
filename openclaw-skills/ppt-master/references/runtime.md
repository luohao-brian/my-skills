# Runtime Contract

## Python capability

The calling runtime owns its Python executable, environment, dependency manager,
browser installation, and process lifecycle. PPT Master consumes that capability;
it does not provision or select it.

- Reuse the Python invocation already selected by the caller. It may be
  `python3`, `python`, `uv run python`, a managed virtual environment, a
  container command, or another compatible runtime-owned launcher.
- Do not create, activate, delete, or relocate a virtual environment; install or
  upgrade packages; alter `PATH`; switch interpreters; or download a browser
  unless the user explicitly requests environment setup or the calling runtime's
  own approved dependency mechanism performs it.
- `requirements.txt` declares Python packages for runtimes that need dependency
  metadata. It does not prescribe an installation directory, package manager, or
  environment layout.
- Before a selected route runs, check only the imports and executables that route
  needs. If one is unavailable, report the missing capability and affected stage.
  Do not classify a missing dependency as a corrupt project asset and do not
  mutate the caller's environment as an implicit recovery step.
- Browser checks may reuse a browser already exposed by the runtime, installed
  Chrome, or Playwright-managed Chromium. If none is available, report that the
  browser-dependent check was not run.

Command examples use `python3` as a readable placeholder. Replace it with the
caller's existing Python invocation; the examples do not require a particular
executable name or a persistent shell activation.

## Project location

Resolve the project root before initialization. Prefer the user-selected output directory; otherwise use a dedicated directory inside the current runtime workspace. Never use `{baseDir}/projects`, a relative `projects/`, or a source-repository directory.

```bash
PROJECTS_ROOT="<caller-selected directory or runtime workspace>"
python3 {baseDir}/scripts/project_manager.py init <name> --format ppt169 --dir "$PROJECTS_ROOT"
```

Pass the resulting absolute project path to every subsequent command.

## Runtime media

Read [`runtime-media.md`](runtime-media.md) before AI image or narration work. Discover the caller's available tools/skills and adapt to their declared schemas. The workflow may request an image or TTS capability, but must not bind itself to an Agent product, provider, model, key, or one fixed parameter spelling.

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
