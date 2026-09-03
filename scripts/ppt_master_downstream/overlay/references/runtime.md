# Downstream Runtime Contract

Use the pinned upstream routes, authoring rules, font selection, quality checks,
and export commands. This runtime contract owns project directories, dependency
discovery, and Agent Plan media execution.

## Mandatory load order

1. Read [`runtime-directory.md`](runtime-directory.md) before project creation or
   any command that resolves a project path.
2. Read [`runtime-dependencies.md`](runtime-dependencies.md) before invoking
   Python, a browser, image generation/search, TTS, or another runtime tool.

`{baseDir}` always means the absolute directory containing this Skill. An
upstream command beginning with `scripts/` resolves to `{baseDir}/scripts/`; an
upstream reference beginning with `templates/`, `references/`, or `workflows/`
resolves the same way. In upstream script help, `skills/ppt-master/` also refers
to `{baseDir}/`. Never infer the Skill path from CWD.

## Failure reporting

Report the exact command and exit code, affected page/element when available,
whether the issue is blocking or advisory, artifacts not produced, and the
recovery action. Apply the selected upstream route's required checks and report
any unavailable capability at its affected stage.
