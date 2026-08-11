# Runtime TTS Contract

PPT Master keeps upstream narration orchestration and adds a narrow Volcengine
Agent Plan execution adapter. Invoke `notes_to_audio.py`; do not route narration
through a separate skill or host-native TTS tool. The fixed endpoint is
`https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional`, the fixed
model/resource is `seed-tts-2.0`, and authentication reads only
`ARK_AGENT_PLAN_API_KEY` for the `X-Api-Key` header. Do not read backend selector,
provider bridge, normal Ark, or legacy speech variables.

The backend publishes MP3 at 24 kHz by default and enforces the provider's 4000
character per-slide ceiling. It currently records audio-only narration in the
upstream manifest. Never fabricate subtitle timing. A failed request must leave
no partial audio target and must not silently switch profiles, credentials,
voice, or model.
