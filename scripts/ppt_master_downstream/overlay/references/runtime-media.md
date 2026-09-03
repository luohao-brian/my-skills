# Agent Plan Media

Select `ark-agent-plan` only when the caller configures or requests Agent Plan.
Check `ARK_AGENT_PLAN_API_KEY` when invoking that service; it is optional for
other services and for tasks that do not generate media. Keep credentials in
the runtime environment or its selected `.env`, outside the Skill source.

## Images

Use `image_gen.py --backend ark-agent-plan`, or set
`IMAGE_BACKEND=ark-agent-plan`. The adapter uses
`https://ark.cn-beijing.volces.com/api/plan/v3/images/generations` and
`doubao-seedream-5.0-lite`. It accepts the upstream Volcengine `2K` and `4K`
size presets; unsupported sizes produce an error. Use the upstream image
manifest and generation commands.

## Narration

Use `notes_to_audio.py --provider ark-agent-plan`, or set
`TTS_PROVIDER=ark-agent-plan`. The adapter uses
`https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional` and the
`seed-tts-2.0` resource. Authentication sends `ARK_AGENT_PLAN_API_KEY` in the
`X-Api-Key` header.

The adapter publishes MP3 at 24 kHz by default and accepts at most 4000
characters per slide. Set `--voice-id` to select a voice and
`--volcengine-sample-rate` to select a sample rate. It records audio-only
narration in the upstream manifest; never fabricate subtitle timing. Report a
failed request without silently switching services or credentials.
