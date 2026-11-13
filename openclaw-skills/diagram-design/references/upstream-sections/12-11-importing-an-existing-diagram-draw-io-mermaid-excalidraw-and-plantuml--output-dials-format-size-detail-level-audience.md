<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Output dials — format, size, detail level, audience`

### Output dials — format, size, detail level, audience

Set these four import decisions **before** drawing. Full spec: [output-spec.md](../../upstream/references/output-spec.md).

| Dial | Options | Default |
|---|---|---|
| **Format** | `html` · `svg` · `png` · `html+png` | `html` |
| **Size** | `doc-inline` · `doc-wide` · `slide-16x9` · `slide-4x3` · `social-og` · `social-square` · `print-a4-landscape` · `print-a3-landscape` · `print-letter-landscape` · `fit` | `doc-inline` |
| **Detail** | `faithful` (≤24 nodes, zoned) · `balanced` (≤12) · `simplified` (≤7) | `balanced` |
| **Audience** | `engineer` · `mixed` · `executive` — governs wording, not count | `mixed` |

The size preset sets the `viewBox` **and** the type ramp; `faithful` is the only exemption from the §7 budget — zoned above 9 nodes, split above 24. The §6 connector rules never relax.

---
