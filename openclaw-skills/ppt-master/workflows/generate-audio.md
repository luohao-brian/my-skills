---
description: Generate one narration file per slide with the runtime TTS tool, verify duration and coverage, then optionally embed the audio into PPTX
---

# Generate Audio Workflow

Use this workflow when the user asks for narration, a narrated PPT, or a video-ready PPTX.

## Required capability

- A TTS tool must be present in the current runtime.
- The skill does not contain a TTS provider, voice catalog, model selector, API client, or provider fallback.
- Do not ask the user to choose a provider, model, voice ID, endpoint, or API key.
- If the TTS tool is absent, stop and report that narration could not be generated.

## Step 1 — Prepare page tasks

`notes/*.md` must contain one file per slide. Split `notes/total.md` first when needed.

```bash
python3 {baseDir}/scripts/total_md_split.py <project_path>
python3 {baseDir}/scripts/audio_manifest.py prepare <project_path>
python3 {baseDir}/scripts/audio_manifest.py pending <project_path>/audio/audio_tasks.json
```

`prepare` creates `audio/audio_tasks.json`. Each task contains:

- `slide`: page identifier
- `text`: spoken text with Markdown headings removed
- `output_path`: absolute preferred MP3 path under `<project_path>/audio/`; `record` keeps a returned M4A or WAV when the TTS tool uses one of those formats
- `status`: `Pending`, `Generated`, or `Failed`

## Step 2 — Call the TTS tool

For every Pending or Failed task:

1. Call the TTS tool listed by the current runtime.
2. Pass the task's `text`.
3. Pass the task's absolute `output_path` when the tool supports it.
4. Do not pass or select a provider, model, voice, voice ID, rate, endpoint, or API key.
5. If the tool returns a different local file path, record it with:

   ```bash
   python3 {baseDir}/scripts/audio_manifest.py record \
     <project_path>/audio/audio_tasks.json <slide> --source <returned-local-file>
   ```

6. If the tool writes directly to `output_path`, run the same `record` command with that path as `--source`.

When a TTS call fails:

```bash
python3 {baseDir}/scripts/audio_manifest.py fail \
  <project_path>/audio/audio_tasks.json <slide> --error '<tool error>'
```

Stop before embedding while any task is Pending or Failed. Do not install a TTS package or call a provider API from this skill.

## Step 3 — Verify narration

```bash
python3 {baseDir}/scripts/audio_manifest.py verify \
  <project_path>/audio/audio_tasks.json
```

Verification requires:

- one generated audio file for every page note
- non-empty `mp3`, `m4a`, or `wav` files
- a positive duration reported by the available audio metadata reader (`ffprobe`, WAV metadata, or `afinfo`)
- no Pending or Failed task

## Step 4 — Embed when requested

```bash
python3 {baseDir}/scripts/svg_to_pptx.py <project_path> \
  --recorded-narration audio
```

Recorded narration requires object animations to use `after-previous` or `with-previous`, not `on-click`. The export writes a narrated PPTX under `exports/` and uses each verified audio duration for slide advance timing.

## Completion report

Report:

- generated page count
- audio directory
- verification result
- narrated PPTX path when embedded

Do not report a provider, model, voice, or rate; those belong to the runtime's TTS configuration.
