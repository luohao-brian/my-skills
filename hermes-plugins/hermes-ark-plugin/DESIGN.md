# Hermes Ark Plugin Design

## Verdict

The plugin owns direct Ark API and Ark Agent Plan multimedia integration because
Hermes v0.20.x does not provide those backends natively. Hermes continues to
own public tool schemas, file safety, preprocessing, provider dispatch, and
operator consent.

## Capability ownership

| Capability | Integration | Owner of public tool shell |
| --- | --- | --- |
| TTS | `ctx.register_tts_provider` | Hermes |
| STT | `ctx.register_transcription_provider` | Hermes |
| Image generation | `ctx.register_image_gen_provider` | Hermes |
| Video generation | `ctx.register_video_gen_provider` | Hermes |
| Image understanding | authorized `vision_analyze` override | Ark plugin, schema imported from Hermes |
| Video understanding | authorized `video_analyze` override | Ark plugin, schema imported from Hermes |

`transcribe_audio` is not overridden. The Ark provider receives the normalized,
validated file from Hermes' native transcription dispatcher.

## Registration flow

`register(ctx)` stores the v2 namespaced config facade and always registers all
four providers. It probes `ctx.has_capability("tools.override")` before
registering the understanding overrides. A missing grant therefore degrades to:

- Ark TTS/STT/image/video generation available.
- Hermes-native image/video understanding unchanged.
- Plugin load succeeds in fresh or non-interactive profiles.

## Backend contract

Every section has a `backend` setting. The default is `ark-agent-plan`.
Credential selection is strict:

- Agent Plan: `ARK_AGENT_PLAN_API_KEY` for every section.
- Ark API media/vision: `ARK_API_KEY`.
- Ark API speech: `ARK_TTS_X_API_KEY`.

No request retries against another backend or credential family.

## Media safety

Understanding overrides call `tools.image_source.resolve_image_source` with
the active `task_id`. That preserves Hermes' local/remote terminal boundary,
credential-file guard, SSRF policy, MIME sniffing, data-URL validation, and
50 MB ingest cap. Image region crops occur only after safe resolution. Network
calls run off the async event loop, and interruption is checked before upload.

Generation providers apply Hermes' credential-file guard before converting a
local reference image to a data URL. Generated URL media is materialized into
Hermes' cache before reporting success.

## Protocol alignment

- Vision and video understanding use multimodal Chat Completions.
- Seedream Lite uses nested
  `sequential_image_generation_options.max_images`; Pro stays single-image.
- Seedance Agent Plan embeds `--dur`, `--ratio`, and `--rs`; Ark API sends
  structured task fields.
- BigASR receives 16 kHz, mono, signed 16-bit PCM in paced 200 ms packets while
  a concurrent reader consumes provider frames.
- TTS parses audio and timing events from the same Seed-TTS 2.0 stream.

## Upgrade boundary

If a future Hermes release adds first-class direct Ark providers, the matching
plugin provider should be removed and Hermes' native implementation selected.
Model availability through a third-party gateway does not satisfy this boundary:
native coverage must support the same Ark credentials, endpoints, and entitlement
semantics.
