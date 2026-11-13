<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Reference Images`

## Reference Images

Accept via `--ref <files...>`, file paths, or pasted images (guide style, palette, composition, or subject):
- File path(s) → copy to `refs/NN-ref-{slug}.{ext}` alongside the output
- Pasted image with no path → ask for the path (per User Input Tools), or extract style traits verbally as a text fallback

| Usage | Effect |
|-------|--------|
| `direct` | Pass the file to the backend as a reference image |
| `style` | Extract style traits (line treatment, texture, mood) and append to the prompt body |
| `palette` | Extract hex colors from the image and append to the prompt body |

Record refs in `prompts/infographic.md` frontmatter:

```yaml
references:
  - ref_id: 01
    filename: 01-ref-brand.png
    usage: direct
```

At generation: verify each referenced file exists; if `usage: direct` AND the backend accepts reference images (e.g., `baoyu-image-gen` via `--ref`), pass it via the backend's ref parameter; otherwise embed extracted `style`/`palette` traits in the prompt text.
