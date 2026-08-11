# Target-Host Font Contract

PPTX does not embed the authored CSS fallback stack. The target application
writes and resolves concrete Latin, East Asian, and complex-script faces, so
font selection is a host policy rather than a browser-only styling choice.

## Selection and execution

- Before accepting typography, run `font_preflight.py` for every distinct
  concrete face required by a recurring role.
- Every stack that can render East Asian text must explicitly name an installed
  East Asian face. Generic `sans-serif`, `serif`, or `monospace` tails do not
  satisfy the PowerPoint contract.
- Mixed-script text must validate both its Latin face and its East Asian face.
- A missing family, silent substitute, legacy coverage face, or synthesized
  emphasis weight is blocking for generated pages.
- Preserve explicit target-host faces during export. Cross-platform alias maps
  are import/migration aids, not release-time rewrites.

```bash
python3 {baseDir}/scripts/font_preflight.py \
  --family "<latin-face>" --family "<east-asian-face>" \
  --require-emphasis --json
```

The downstream SVG checker reports structured findings with file, element,
source stack, detected scripts, resolved faces, host assessment, and remediation.
Repair the owning typography plan or SVG and rerun the complete preflight.

Host availability and portability are separate facts. A face may be approved
and installed on the selected target while remaining unavailable on another OS;
never report a static allowlist result as target-host availability.
