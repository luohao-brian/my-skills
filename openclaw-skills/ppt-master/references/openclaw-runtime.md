# OpenClaw Runtime Contract

## Upstream baseline

- Repository: `https://github.com/hugohe3/ppt-master`
- Imported commit: `85cf22eaf4a74a511c4bff9b33a15fc0f7b33e87`
- Imported at: `2026-07-15`
- Hermes comparison: the Hermes-installed `SKILL.md` was older than this baseline; the OpenClaw copy starts from the GitHub baseline and adds the release checks below.

## Install dependencies

Use a dedicated Python environment. Do not install into the source tree.

```bash
python3 -m venv <external-cache>/ppt-master-venv
<external-cache>/ppt-master-venv/bin/python -m pip install -r {baseDir}/requirements.txt
<external-cache>/ppt-master-venv/bin/python -m playwright install chromium
```

The layout audit also tries an installed Google Chrome channel when Playwright's managed Chromium is unavailable.

## Keep projects outside source repositories

Resolve an absolute project root before initialization. Use the user's requested output directory; otherwise use a workspace such as `~/hermes-workspace` or an OS temporary directory. Never use `{baseDir}/projects`, the current source repository, or a relative `projects/` path.

```bash
PROJECTS_ROOT="<absolute external directory>"
python3 {baseDir}/scripts/project_manager.py init <name> --format ppt169 --dir "$PROJECTS_ROOT"
```

Pass the resulting absolute project path to every later command. Preview, review, backup, and export artifacts then remain inside that external project.

## Release gate

Run these against authored `svg_output/` before finalization:

```bash
python3 {baseDir}/scripts/project_manager.py validate <project>
python3 {baseDir}/scripts/svg_quality_checker.py <project>
python3 {baseDir}/scripts/visual_layout_audit.py <project>
```

The static checker owns SVG/PPTX compatibility, inline-style validity, forbidden CSS/classes, `viewBox`, IDs, fonts, and `spec_lock` drift. The browser audit owns rendered geometry:

- visible elements outside the SVG canvas or browser viewport;
- text/text collisions and container-like group overflow;
- broken or zero-size rendered elements;
- multi-viewport scaling at `1280x720`, `1024x768`, `1440x900`, and `720x1280`;
- content-span underuse and edge crowding.

Errors block export. Warnings require one of: fix, confirm intentional design, or record a concise release note. Do not silently ignore warnings.

After export, inspect the actual PPTX geometry:

```bash
python3 {baseDir}/scripts/pptx_layout_audit.py <project>/exports/<deck>.pptx
```

This checks slide dimensions, shapes outside slide bounds, text-frame collisions, and spatial utilization in the generated package. Fix the SVG source and re-export when the native PPTX audit finds a problem.

## Visual review

Use `workflows/visual-review.md` after the deterministic release gate when human-level judgement is still needed for contrast, hierarchy, narrative emphasis, or image meaning. Deterministic checks are mandatory; judgement review is an additional layer.

## Failure reporting

Report:

1. the exact command and exit code;
2. the affected page and element IDs when available;
3. whether the issue is a blocking geometry/style error or a judgement warning;
4. which artifacts were not produced.
