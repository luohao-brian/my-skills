# Ark STT Reference

## Environment

Required:

- `ARK_AGENT_PLAN_API_KEY`

The script reads only `ARK_AGENT_PLAN_API_KEY` for authentication.

Optional:

- `VOLC_STT_BASE_URL`: defaults to `wss://openspeech.bytedance.com/api/v3/plan/sauc/bigmodel_nostream`
- `VOLC_STT_RESOURCE_ID`: defaults to `volc.seedasr.sauc.duration`

## Usage

```bash
python3 {baseDir}/scripts/volc_stt.py ./meeting.wav
python3 {baseDir}/scripts/volc_stt.py ./voice.ogg --format ogg --codec opus
python3 {baseDir}/scripts/volc_stt.py ./clip.mp3 --seg-duration-ms 200
```

## Audio Hints

- `wav`, `pcm`, and `mp3` default to codec `raw`.
- `ogg` and `opus` default to codec `opus`.
- The default sample rate in the request metadata is `24000`.
- The script sends chunked binary frames and waits for the final package.

## Failure Reporting

Report:

- Missing `ARK_AGENT_PLAN_API_KEY`.
- Empty input file.
- WebSocket connection errors.
- Non-zero ASR response codes.
- Empty final transcript.
