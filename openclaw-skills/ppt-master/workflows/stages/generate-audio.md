---
description: Runtime-neutral narration generation, verification, PPTX embedding, and optional video export.
---

# Generate Audio Stage

Run only when the selected route or the user enables narration. This stage consumes complete per-slide speaker notes and discovers a compatible TTS tool/skill in the current Agent. It never binds the workflow to an Agent, provider, model, credential, or voice implementation.

Read [`../../references/runtime-media.md`](../../references/runtime-media.md) first.

## Preconditions

- Every expected slide has a non-empty `notes/<slide>.md` file. Generate PPTX first splits `notes/total.md`; Native Enhance writes numeric files directly.
- Each slide's spoken text is at most 4000 characters. Shorten that slide's narration instead of sending an oversized request.
- The current Agent exposes at least one compatible TTS tool/skill; read its schema/instructions before use.
- `ffprobe` is available when narration is embedded, because slide duration is derived from actual audio.

## 1. Prepare deterministic tasks

```bash
python3 {baseDir}/scripts/audio_manifest.py prepare <absolute-project>
python3 {baseDir}/scripts/audio_manifest.py check <absolute-project>/audio/audio_tasks.json
python3 {baseDir}/scripts/audio_manifest.py pending <absolute-project>/audio/audio_tasks.json
```

`pending` emits one provider-neutral semantic request per slide:

```json
{"text":"<speaker-note narration>","preferred_output_path":"<absolute project audio path>"}
```

The output path must remain inside the active runtime workspace/project.

## 2. Call runtime TTS and record results

For every pending task, discover compatible TTS capabilities, preflight configured providers when supported, and map `capability_request` to the selected capability's real schema. `preferred_output_path` is optional when the capability chooses its own destination. Follow that capability's own instructions. After it returns a local file:

```bash
python3 {baseDir}/scripts/audio_manifest.py record \
  <absolute-project>/audio/audio_tasks.json <slide> --source <returned-audio-path>
```

On a runtime failure, preserve a concise task-level error:

```bash
python3 {baseDir}/scripts/audio_manifest.py fail \
  <absolute-project>/audio/audio_tasks.json <slide> --error "<concise runtime error>"
```

Do not switch providers inside PPT Master. When the runtime returns a sibling `.transcript.json`, `record` preserves its path. Audio-only output is valid; never invent word timing.

## 3. Verify and embed

```bash
python3 {baseDir}/scripts/audio_manifest.py verify <absolute-project>/audio/audio_tasks.json
python3 {baseDir}/scripts/svg_to_pptx.py <absolute-project> \
  --recorded-narration audio --narration-padding 0.5 \
  --inherit-motion-from <absolute-base-postflight-report>
```

If canonical `animations.json` is active, narration-cued animation/subtitle synchronization requires usable timing artifacts. With suitable page-local timings, derive the sidecars via `narration_sync.py`; with audio only, preserve ordinary animation and embed narration without fabricating cue mappings. Explicit all-motion-off uses `--no-animations`.

Run the PPTX delivery and layout checks again on the narrated export.

## 4. Optional native video

Only offer automatic video when the platform check succeeds:

```bash
python3 {baseDir}/scripts/powerpoint_video.py --check
```

On supported Windows PowerPoint:

```bash
python3 {baseDir}/scripts/powerpoint_video.py <absolute-narrated-pptx> -o <absolute-video.mp4>
```

macOS does not provide the equivalent PowerPoint automation contract. Report that limitation rather than substituting UI scripting.

## Completion

Report the generated/failed slide count, verified audio paths and durations, whether timing artifacts were available, the narrated PPTX path, and any video-export limitation.
