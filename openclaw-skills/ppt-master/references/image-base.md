> See [`image-generator.md`](./image-generator.md) and [`image-searcher.md`](./image-searcher.md) for path-specific behavior.

# Image Acquisition Common Reference

Shared baseline for both acquisition paths. Path-specific behavior lives in the path's own reference.

---

## 1. Trigger Condition

Active when at least one resource list row has `Acquire Via: ai` / `web` / `slice`. Rows with `user` / `formula` / `placeholder` are skipped.

| Mode | Trigger |
|---|---|
| In-pipeline | `generate-ppt` workflow, image rows present |
| Standalone | Direct request against an existing project |

---

## 2. Image Resource List Format

Defined in `design_spec.md §VIII`. Status enum: see [`svg-image-embedding.md`](svg-image-embedding.md).

| Filename | Dimensions | Purpose | Type | Acquire Via | Status | Reference |
|---|---|---|---|---|---|---|
| cover.png | 1280x720 | Cover background | Background | `ai` | Pending | Modern tech abstract, deep blue gradient #0A2540 |
| team.jpg | 800x600 | Team photo | Photography | `web` | Pending | Diverse engineering team in modern office |
| formula_001.png | 736x168 | Block equation on P03 | Latex Formula | `formula` | Rendered | `E = mc^2` |
| spot_team.png | TBD after slicing | Team spot illustration | Illustration | `slice` | Pending | From `spot_sheet.png` cell 1,1 |

**Required per non-skipped row**: `Acquire Via`, `Status`, `Reference`.

---

## 3. Path Dispatch

For each row with `Status: Pending`:

| Acquire Via | Load reference | Run | Success status |
|---|---|---|---|
| `ai` | [`image-generator.md`](./image-generator.md) | runtime image-generation tool + `image_manifest.py` | `Generated` |
| `web` | [`image-searcher.md`](./image-searcher.md) | `image_search.py` | `Sourced` |
| `slice` | [`image-generator.md`](./image-generator.md) §4.3 | `slice_images.py` after parent AI sheet is `Generated` | `Generated` |
| `user` | — | — | (already `Existing`) |
| `formula` | — | — | (already `Rendered`) |
| `placeholder` | — | — | (already `Placeholder`) |

> Lazy load: an all-`web` deck never reads `image-generator.md`, and vice versa.

---

## 4. Analysis Phase

Before processing any row:

1. `read_file <project_path>/design_spec.md` — extract color scheme, canvas format, target audience
2. Group resource list rows by `Acquire Via`
3. Confirm `project/images/` exists

---

## 5. Verification Phase

After all rows reach terminal status:

- Every `ai` and `slice` row has a file at `project/images/<filename>` and is `Generated`
- Every failed `web` row is either replaced or marked `Needs-Manual`
- No `Pending` or `Failed` rows remain
- `image_prompts.json` exists when ≥1 ai row processed; every entry has `status: Generated`
- `image_sources.json` exists when ≥1 web row processed; every entry has `license_tier ∈ {no-attribution, attribution-required, manual}` (`manual` = a user-supplied `--from-url` replacement)

> AI image rows never use `Needs-Manual`. They require the runtime's image-generation tool and block Executor until generated.

---

## 6. Failure Handling

**Hard rule**: an AI image failure stops AI acquisition before Executor. Web search failures may still use `Needs-Manual`.

1. Try once
2. On recoverable failure (network, no candidates, license rejection, rate limit), retry once with broadened parameters
3. For an `ai` row, record `Failed` with `image_manifest.py fail`, report the image-tool error, and stop before Executor.
4. For a `web` row, follow `image-searcher.md`; after its retry limit it may become `Needs-Manual`.

---

## 7. Credits — Single Source of Truth

License / attribution data lives **only** in `project/images/image_sources.json`.

**Forbidden — credits anywhere else**:

- `notes/*.md` (TTS would speak them in the audio export)
- `total.md` (gets split, then overwritten)
- SVG `<title>` / `<desc>` (stripped by `svg_to_pptx.py`)
- A separate "Image Credits" appendix slide (lost on single-page sharing)

Executor reads the manifest per slide and renders inline credits when needed — see [`executor-base.md`](./executor-base.md) §6.1 and [`image-searcher.md`](./image-searcher.md) §7.

---

## 8. Handoff with Strategist

The `Reference` field is **intent**, not a query. Strategist writes free-form intent; the receiving role translates.

| ✅ Intent | ❌ Pre-processed |
|---|---|
| `"Diverse engineering team in modern office, natural light"` | `"team office light"` |
| `"Abstract digital waves, deep navy gradient #0A2540"` | `"use openverse, search 'waves'"` |

---

## 9. Handoff with Executor

Executor consumes the resource list plus:

| Artifact | Path | Purpose |
|---|---|---|
| Image files | `project/images/*.{jpg,png,webp}` | `<image>` references |
| Manifest | `project/images/image_sources.json` | `license_tier` per Sourced image |

Executor does NOT invoke the image-generation tool, `image_search.py`, or `slice_images.py`.

---

## 10. Task Completion Checkpoint

```markdown
## ✅ Image Acquisition Phase Complete
- [x] {N} rows processed (`ai`: {a} / `web`: {b} / `slice`: {s})
- [x] {a} AI `Generated`, {b} web `Sourced`, {s} sliced `Generated`, {c} web `Needs-Manual`
- [x] image_prompts.json / image_sources.json written
- [ ] **Next**: Auto-proceed to Executor phase
```
