# AI Image Generation

Use this reference only for rows whose active resource authority says `Acquire Via: ai`. Read [`runtime-media.md`](runtime-media.md) first. PPT Master owns prompt design, manifest state, placement intent, and file validation; the host runtime owns the provider.

## 1. Deck-wide image identity

Choose one coherent rendering family for the deck and keep it across generated images. A page may change composition or subject, but should not look like it came from an unrelated visual system.

Resolve these inputs before writing prompts:

- deck purpose, audience, narrative tone, and page role;
- SVG canvas palette and intended image color relationship;
- one rendering preset from `image-renderings/` or a precise custom rendering description;
- local composition type from `image-type-templates/` only when it actually fits;
- the planned image container, crop policy, focal point, and required quiet region;
- whether text belongs in SVG (`text_policy: none`) or is intentionally artistic/stable inside the image (`embedded`).

Do not load every preset. Read only the selected rendering/type files.

## 2. Prompt assembly

Write one coherent paragraph, in this order:

1. specific subject, action, environment, and point of view;
2. selected rendering identity, medium, texture, lighting, and detail level;
3. composition/camera instructions matching the actual slide container;
4. deck color-role guidance and restrained contextual tones;
5. text policy, exclusions, and quality constraints.

For `text_policy: none`, end with an explicit prohibition on letters, numbers, labels, captions, logos, watermarks, and UI text. Keep authoritative titles, body copy, data, and long quotations in SVG.

Do not put brand names, API/provider names, model names, or literal HEX strings in the depicted subject. HEX values may guide palette in descriptive form, but must not appear as visible image text.

### Illustration sheets

Several small same-family spot illustrations may be generated as one flat `R×C` sheet, then cut with `slice_images.py`. Use a flat background matched to the slide, equal cells, consistent scale, generous gutters, no overlaps, no labels, and exactly one centered object per cell. The sheet itself is never placed on a slide.

## 3. Manifest

Write `<project>/images/image_prompts.json`:

```json
{
  "project": "daily-ai-news",
  "deck_rendering": "editorial vector collage",
  "color_scheme": {
    "background": "warm off-white",
    "primary": "deep navy",
    "accent": "electric cyan"
  },
  "items": [
    {
      "filename": "cover-hero.png",
      "purpose": "Cover hero",
      "page_role": "hero_page",
      "text_policy": "none",
      "aspect_ratio": "16:9",
      "prompt": "<fully assembled prompt>",
      "status": "Pending"
    }
  ]
}
```

Required per item: `filename`, `prompt`, positive `W:H` `aspect_ratio`, and `status`. Common portable ratios are `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, and `21:9`; other positive ratios remain valid and are adapted to the selected capability. Optional planning fields such as `purpose`, `page_role`, `text_policy`, `type`, `alt_text`, `slice_grid`, and `slice_names` are allowed.

Forbidden manifest fields: `provider`, `backend`, `model`, `api_key`, and `apiKey`.

Validate and render the readable sidecar:

```bash
python3 {baseDir}/scripts/image_manifest.py check <project>/images/image_prompts.json
python3 {baseDir}/scripts/image_manifest.py render-md <project>/images/image_prompts.json
python3 {baseDir}/scripts/image_manifest.py pending <project>/images/image_prompts.json
```

## 4. Runtime execution

`pending` emits a provider-neutral `capability_request`. For each task:

1. discover the current Agent's compatible image tools/skills and read the selected interface;
2. map `capability_request` to that interface's actual field names and supported enum values;
3. follow that capability's own skill/instructions;
4. record the returned local file:

```bash
python3 {baseDir}/scripts/image_manifest.py record \
  <project>/images/image_prompts.json <filename> --source <returned-local-file>
```

On failure:

```bash
python3 {baseDir}/scripts/image_manifest.py fail \
  <project>/images/image_prompts.json <filename> --error "<concise runtime error>"
```

Do not hard-code a provider or Agent inside PPT Master. Ark API, Ark Agent Plan, and MiniMax may be preflighted when their adapters are present, alongside every other compatible configured capability. If none exists, keep the item pending/failed, preserve its prompt sidecar, and report the missing capability. A user may manually supply the expected file; validate and record it through the same command.

## 5. Verification and recovery

```bash
python3 {baseDir}/scripts/image_manifest.py verify <project>/images/image_prompts.json
python3 {baseDir}/scripts/analyze_images.py <project>/images
```

Before SVG authoring, each required AI row must have a verified file and `Generated` status. For an unsatisfactory image, change only the prompt dimension responsible, set that item back to `Pending`, generate a new filename/version, and compare it in the intended slide crop. Do not upscale merely to fake resolution.

Common repairs:

| Symptom | Repair |
|---|---|
| Generic/model-average | Replace tag soup with a concrete scene and visual hierarchy |
| Wrong style | Reassert the chosen rendering family at the start |
| Busy under text | Request a quiet region at the exact overlay position |
| Garbled letters | Strengthen `text_policy: none` exclusions |
| Weak subject | Name concrete actors, objects, action, camera, and setting |
| Palette drift | Restate semantic color roles; remove unrelated accent hues |

## 6. Forbidden

- generating AI prompts for `web` rows;
- writing provider/model/credentials into project artifacts;
- claiming success without a valid local image;
- mixing unrelated rendering families across the deck;
- embedding body copy, data tables, bullets, or long quotes in raster images;
- changing `spec_lock.md` to match an accidental generated-image result.
