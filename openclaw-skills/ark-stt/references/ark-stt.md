# Ark STT Reference

## Backends

| `--backend` | Credential | Endpoint |
| --- | --- | --- |
| `ark-agent-plan` (default) | `ARK_AGENT_PLAN_API_KEY` | `wss://openspeech.bytedance.com/api/v3/plan/sauc/bigmodel_nostream` |
| `ark-api` | `ARK_TTS_X_API_KEY` | `wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_nostream` |

Both backends use resource `volc.seedasr.sauc.duration`. Endpoints are fixed,
and the script does not fall back between backends.

## Request

- Header `X-Api-Resource-Id`: `volc.seedasr.sauc.duration`
- Header `X-Api-Request-Id`: a fresh UUID for each connection
- Header `X-Api-Sequence`: `-1`
- This implementation uses the new-console `X-Api-Request-Id` plus `X-Api-Sequence` request form.
- `X-Api-Connect-Id` is an alternative request correlation header used by compatible examples. This implementation does not need to send it; it is not a response-only field.
- Official Agent Plan API: https://www.volcengine.com/docs/82379/2516286?lang=zh
- Official binary protocol: https://www.volcengine.com/docs/6561/1354869?lang=zh

## Usage

```bash
python3 {baseDir}/scripts/volc_stt.py ./meeting.wav
python3 {baseDir}/scripts/volc_stt.py ./meeting.wav --backend ark-api
python3 {baseDir}/scripts/volc_stt.py ./voice.ogg --format ogg --codec opus
python3 {baseDir}/scripts/volc_stt.py ./clip.mp3 --raw
```

## Audio Hints

- `wav`, `pcm`, and `mp3` default to codec `raw`.
- `ogg` and `opus` default to codec `opus`.
- The request sample rate is fixed to the provider-supported `16000` Hz.
- WAV and PCM input must be uncompressed signed 16-bit mono audio at 16 kHz; MP3 frame headers must also report 16 kHz.
- The script derives duration from PCM or WAV metadata. It preserves complete MP3 frames and Ogg Opus pages when grouping encoded audio into approximately 100-200 ms packages.
- It paces packages by their calculated audio duration while continuously receiving provider frames, then waits for the final package.
- Invalid or mismatched audio metadata fails before audio packages are sent.
- Default output omits the provider payload; `--raw` includes it.

## Failure Reporting

Report:

- The credential missing for the selected backend.
- Empty input file.
- WebSocket connection errors.
- Non-zero ASR response codes.
- Empty final transcript.
