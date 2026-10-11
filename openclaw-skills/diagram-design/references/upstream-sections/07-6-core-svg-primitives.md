<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `6. Core SVG Primitives`

## 6. Core SVG Primitives

Universal building blocks. Type-specialized primitives (lifeline, activation bar, region) live in the relevant type reference linked in the guide. Optional primitives:

- Editorial callouts → [primitive-annotation.md](../../upstream/references/primitive-annotation.md)
- Hand-drawn variant → [primitive-sketchy.md](../../upstream/references/primitive-sketchy.md)
- Icon set (laptop, server, DB, K8s, Docker, AWS, …) → [primitive-icons.md](../../upstream/references/primitive-icons.md). Browse the gallery at [`assets/icons.html`](../../upstream/assets/icons.html).
- Terminal / CLI-window variant → [primitive-terminal.md](../../upstream/references/primitive-terminal.md)
- Optional explanatory motion → [animation.md](../../upstream/references/animation.md)

Exact markup (background, dotted paper, markers, node box, arrow label, legend) and the long form of each connector rule: [`references/primitives-core.md`](../../upstream/references/primitives-core.md). The static templates (`template.html`, `template-dark.html`, `template-full.html`) already define the background and the `arrow`, `arrow-accent`, and `arrow-link` markers; `template-motion.html` defines only its own prefixed marker, so add the others from primitives-core.md when a motion diagram needs them.

- **Arrows:** `muted` by default, `accent` for the headline path, `link` for HTTP/API and external calls, dashed `5,4` for optional, passive, return, or async. Draw arrows before boxes so lines sit behind nodes.
- **Node box:** an opaque paper mask rect, then the styled box at `rx=6`, a rectangular type tag at `rx=2` (not a pill), the name in Geist 600, and a Geist Mono sublabel.
