# Runtime Media Capability Contract

PPT Master describes required media outcomes. The current Agent and its installed tools/skills own provider discovery, credentials, models, voices, transport, retries, and billing. Never assume a particular Agent product or provider.

## Capability discovery and preflight

Before generation:

1. Inspect the tools and skills actually available in the current turn/runtime.
2. Select capabilities that explicitly support image generation or text-to-speech. Honor a user-selected capability first.
3. Read the selected tool schema or skill instructions before constructing a call.
4. When the capability exposes status/provider discovery, preflight every configured compatible provider rather than assuming one. Ark API, Ark Agent Plan, and MiniMax are known compatibility cases, not required dependencies or preferred providers.
5. Map the semantic request below to the capability's real field names and enums. Do not pass unsupported fields merely because another runtime accepts them.
6. Record and verify the returned local artifact through the PPT Master manifest helper.

If several compatible capabilities are available and the user did not choose one, prefer an already configured, healthy capability that best satisfies the requested aspect ratio/quality or timing needs. Do not silently change acquisition type after an explicit user choice.

## Image semantic request

Each pending task declares:

```json
{
  "prompt": "<complete generation prompt>",
  "aspect_ratio": "16:9",
  "count": 1,
  "preferred_output_path": "<absolute project image path>"
}
```

Adapter examples, chosen only when the actual schema supports them:

- `aspect_ratio` may map to `size`, `aspect_ratio`, width/height, or the closest supported preset.
- `count` may map to `max_images`, `n`, or one repeated call.
- A capability that chooses its own output path is valid; record its returned local file afterward.
- Optional reference inputs may map to `images`, `image`, or the capability's documented reference-image field.

The common portable aspect ratios are `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, and `21:9`, but any positive `W:H` request is valid. When a selected capability cannot produce the exact ratio, use its closest documented preset and preserve the requested ratio for layout/cropping; report the adaptation.

Provider/model/key fields never belong in the project manifest.

## TTS semantic request

Each pending task declares:

```json
{
  "text": "<speaker-note narration>",
  "preferred_output_path": "<absolute project audio path>"
}
```

Map `preferred_output_path` only when the selected capability accepts an output path. Otherwise record the returned local artifact. Inspect the capability's declared text limit; PPT Master's portable ceiling is 4000 characters per slide request, and a stricter capability limit wins.

When the selected capability returns transcript, word, sentence, or subtitle timing, preserve the timing artifact. Audio-only output is valid for narration embedding; subtitle/animation synchronization is capability-gated and must never fabricate timing.

## Known compatibility prechecks

These are non-exclusive regression targets, not runtime bindings:

- Ark image/TTS through either direct API or Agent Plan adapters when those capabilities are installed and configured;
- MiniMax image/TTS through an installed runtime adapter;
- any other image/TTS tool or skill whose declared schema can satisfy the semantic request.

PPT Master must not read provider credentials directly or encode provider-specific environment variables. The owning tool/skill performs its own readiness check and reports actionable errors.

## Failure behavior

- No capability: keep the task unresolved and report the missing semantic capability.
- Installed but unconfigured/unhealthy: report that capability's preflight result; try another compatible configured capability only when the user did not pin the first one.
- Runtime generation failure: record the concise task error and follow the selected capability's retry policy.
- Returned file: record it, verify actual format/dimensions or duration, and continue.
- Never replace AI generation with unrelated stock media or another acquisition type without an explicit workflow rule or user approval.
