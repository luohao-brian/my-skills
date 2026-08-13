<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Output Directory`

## Output Directory

Output directory is determined by `default_output_dir` in EXTEND.md (set during first-time setup):

| `default_output_dir` | Output Path | Markdown Insert Path |
|----------------------|-------------|----------------------|
| `imgs-subdir` (default) | `{article-dir}/imgs/` | `imgs/NN-{type}-{slug}.png` |
| `same-dir` | `{article-dir}/` | `NN-{type}-{slug}.png` |
| `illustrations-subdir` | `{article-dir}/illustrations/` | `illustrations/NN-{type}-{slug}.png` |
| `independent` | `illustrations/{topic-slug}/` | `illustrations/{topic-slug}/NN-{type}-{slug}.png` (relative to cwd) |

All auxiliary files (outline, prompts) are saved inside the output directory:

```
{output-dir}/
├── outline.md
├── prompts/
│   └── NN-{type}-{slug}.md
└── NN-{type}-{slug}.png
```

When input is **pasted content** (no file path), always uses `illustrations/{topic-slug}/` with `source-{slug}.{ext}` saved alongside.

**Slug**: 2-4 words, kebab-case. **Conflict**: append `-YYYYMMDD-HHMMSS`.
