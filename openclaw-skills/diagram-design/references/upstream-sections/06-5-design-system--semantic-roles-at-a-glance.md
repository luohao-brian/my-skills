<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Semantic roles (at a glance)`

### Semantic roles (at a glance)

| Role | Purpose |
|---|---|
| `paper`, `paper-2` | Page bg and container bg |
| `ink` | Primary text / stroke |
| `muted`, `soft` | Secondary text, default arrows, sublabels |
| `rule`, `rule-solid` | Hairline borders |
| `accent`, `accent-tint` | 1–2 focal elements per diagram |
| `link` | HTTP/API calls, external arrows |

**Focal rule:** `accent` goes on 1–2 elements max. Everything else is `ink` / `muted` / `soft`. If you're tempted to accent 4 things, you haven't decided what's focal yet.

**Node treatments** (focal, backend/API/step, store/state, external/cloud, input/user, optional/async, security/boundary): fill and stroke per [style-guide.md § Node type → treatment](../../upstream/references/style-guide.md#node-type--treatment).

**Typography:** Instrument Serif for the H1 title and italic callouts, Geist sans 600 for node names, Geist Mono for sublabels, eyebrows, and arrow labels. Sizes, weights, and the font `<link>`: [style-guide.md § Typography](../../upstream/references/style-guide.md#typography); per-preset type ramp: [output-spec.md](../../upstream/references/output-spec.md). When the user asks for offline output, system fonts, or no Google Fonts, follow [style-guide.md § Font source](../../upstream/references/style-guide.md#font-source).

**Non-Latin labels** — extend the family: [Korean](../../upstream/references/style-guide.md#korean-labels), [Chinese](../../upstream/references/style-guide.md#traditional-chinese-labels), [Cyrillic](../../upstream/references/style-guide.md#cyrillic-labels).

**Mono is for technical content only** — never as a blanket "dev" font, and never JetBrains Mono.

---
