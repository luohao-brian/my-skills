# Volcengine Media Routing

## Images

Use the downstream `volcengine` backend for image generation. It defaults to
Ark Agent Plan, Seedream 5.0 Pro, and the shared Agent Plan credential:

```dotenv
ARK_AGENT_PLAN_API_KEY=<agent-plan-key>
```

The effective image defaults are:

```dotenv
IMAGE_BACKEND=volcengine
VOLCENGINE_BASE_URL=https://ark.cn-beijing.volces.com/api/plan/v3/images/generations
VOLCENGINE_MODEL=doubao-seedream-5.0-pro
```

Keep the credential in the selected `.env`, outside the Skill source. These
variables are optional overrides; normal OpenClaw use only needs
`ARK_AGENT_PLAN_API_KEY`.

## Narration (TTS)

`notes_to_audio.py` defaults to `ark-agent-plan`; use
`--provider ark-agent-plan` or `TTS_PROVIDER=ark-agent-plan` explicitly if needed.
This adapter uses the same `ARK_AGENT_PLAN_API_KEY` credential,
`https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional`, and the
`seed-tts-2.0` resource. It does not fall back to another TTS service.

The adapter publishes MP3 at 24 kHz by default and accepts at most 4000
characters per slide. Set `--voice-id` to select a voice and
`--volcengine-sample-rate` to select a sample rate. It records audio-only
narration in the upstream manifest; never fabricate subtitle timing.
