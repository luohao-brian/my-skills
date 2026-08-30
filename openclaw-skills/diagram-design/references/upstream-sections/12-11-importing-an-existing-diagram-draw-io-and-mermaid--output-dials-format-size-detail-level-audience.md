<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Output dials — format, size, detail level, audience`

### Output dials — format, size, detail level, audience

Every imported diagram is shaped by four decisions. Full spec in [`references/output-spec.md`](../../upstream/references/output-spec.md); set them **before** drawing, since they change the deliverable, layout, density, and wording.

| Dial | Options | Default |
|---|---|---|
| **Format** | `html` · `svg` · `png` · `html+png` | `html` |
| **Size** | `doc-inline` · `doc-wide` · `slide-16x9` · `slide-4x3` · `social-og` · `social-square` · `print-a4-landscape` · `print-letter-landscape` · `fit` | `doc-inline` |
| **Detail** | `faithful` (≤24 nodes, zoned) · `balanced` (≤12) · `simplified` (≤7) | `balanced` |
| **Audience** | `engineer` · `mixed` · `executive` — governs wording, not count | `mixed` |

Two consequences: the size preset sets the `viewBox` **and** the type ramp (a slide gets 16px node names, not 12px), and `faithful` is the only exemption from the §7 budget — conditional, zoned above 9 nodes, split above 24. The §6 connector rules never relax.

---
