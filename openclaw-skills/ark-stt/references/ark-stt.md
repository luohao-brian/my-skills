# Ark STT Reference

## Environment

Required:

- `ARK_AGENT_PLAN_API_KEY`

The script reads only `ARK_AGENT_PLAN_API_KEY`. No optional environment variable
is used.

## Request

- Endpoint: `wss://openspeech.bytedance.com/api/v3/plan/sauc/bigmodel_nostream`
- Header `X-Api-Key`: `ARK_AGENT_PLAN_API_KEY`
- Header `X-Api-Resource-Id`: `volc.seedasr.sauc.duration`

## Usage

```bash
python3 {baseDir}/scripts/volc_stt.py ./meeting.wav
python3 {baseDir}/scripts/volc_stt.py ./voice.ogg --format ogg --codec opus
python3 {baseDir}/scripts/volc_stt.py ./clip.mp3 --raw
```

## Audio Hints

- `wav`, `pcm`, and `mp3` default to codec `raw`.
- `ogg` and `opus` default to codec `opus`.
- The default sample rate in the request metadata is `24000`.
- Use `--sample-rate` when the input audio has another sample rate.
- The script sends chunked binary frames at a fixed cadence and waits for the final package.
- Default output omits the provider payload; `--raw` includes it.

## Failure Reporting

Report:

- Missing `ARK_AGENT_PLAN_API_KEY`.
- Empty input file.
- WebSocket connection errors.
- Non-zero ASR response codes.
- Empty final transcript.
