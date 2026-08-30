# Downstream Runtime Contract

This distribution preserves the pinned upstream workflow and changes only three
runtime-owned boundaries: Directory, Font, and Dependency. These rules override
upstream examples only inside those boundaries; upstream route, artifact, design,
and execution rules remain authoritative everywhere else.

## Mandatory load order

1. Read [`runtime-directory.md`](runtime-directory.md) before project creation or
   any command that resolves a project path.
2. Read [`runtime-fonts.md`](runtime-fonts.md) before typography confirmation,
   SVG authoring, validation, or export.
3. Read [`runtime-dependencies.md`](runtime-dependencies.md) before invoking
   Python, a browser, image generation/search, TTS, or another runtime tool.

`{baseDir}` always means the absolute directory containing this Skill. An
upstream command beginning with `scripts/` resolves to `{baseDir}/scripts/`; an
upstream reference beginning with `templates/`, `references/`, or `workflows/`
resolves the same way. Never infer the Skill path from CWD.

## Downstream release gate

## Formal SVG-route publication

Formal SVG-route publication uses the additive orchestrator, not the upstream
exporter directly:

```bash
python3 {baseDir}/scripts/downstream_release.py export <absolute-project> -- <upstream svg_to_pptx.py arguments>
```

The orchestrator runs the upstream final checker, downstream font/readability
checker, and browser layout audit against the same SVG source before calling the
upstream fail-closed exporter. It then runs package and DrawingML geometry checks
against the emitted PPTX. Direct `svg_to_pptx.py` calls are diagnostic unless
they are invoked by this orchestrator.

If the selected runtime cannot provide a required browser, font-discovery, or
Office rendering capability, report the exact unverified stage. Do not silently
replace a required gate with file existence or exporter exit code.

## Failure reporting

Report the exact command and exit code, affected page/element when available,
whether the issue is blocking or advisory, artifacts not produced, and the
recovery action. The final delivery report includes every explicit capability
waiver and target-host limitation.
