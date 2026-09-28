# Ark Media Routing

## Images

The default image backend is `ark`; `image_gen.py --backend ark` or
`IMAGE_BACKEND=ark` selects it explicitly. This route first
uses `ARK_AGENT_PLAN_API_KEY` at
`https://ark.cn-beijing.volces.com/api/plan/v3/images/generations` with
`doubao-seedream-5.0-lite`. If Agent Plan is unavailable because its key is
missing, authentication or quota fails, or the service fails, retry through
`ARK_API_KEY` at `https://ark.cn-beijing.volces.com/api/v3/images/generations`
with `doubao-seedream-5-0-260128`. Malformed requests do not fall back.
Report both failures if neither service returns an image.

Use `--backend ark-agent-plan` or `--backend ark-api` to select only one service.
The Ark API adapter accepts `2K` and `4K` and adds the requested aspect ratio
to the prompt. The Agent Plan adapter uses the upstream ratio-to-pixel map.
Keep credentials in the runtime environment or selected `.env`, outside the
Skill source. The upstream `volcengine` backend remains an explicit LAS route
and requires `LAS_API_KEY`.

## Narration (TTS)

`notes_to_audio.py` defaults to `ark-agent-plan`; use
`--provider ark-agent-plan` or `TTS_PROVIDER=ark-agent-plan` explicitly if needed.
This adapter uses `ARK_AGENT_PLAN_API_KEY`,
`https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional`, and the
`seed-tts-2.0` resource. It does not fall back to another TTS service.

The adapter publishes MP3 at 24 kHz by default and accepts at most 4000
characters per slide. Set `--voice-id` to select a voice and
`--volcengine-sample-rate` to select a sample rate. It records audio-only
narration in the upstream manifest; never fabricate subtitle timing.
