# Ark TTS Reference

## Environment

Required:

- `VOLC_AGENT_PLAN_API_KEY`

Accepted compatibility fallbacks:

- `ARK_API_KEY`
- `OPENAPI_API_KEY`

Optional:

- `VOLC_TTS_BASE_URL`: defaults to `https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional`
- `VOLC_TTS_RESOURCE_ID`: defaults to `seed-tts-2.0`
- `VOLC_TTS_VOICE`: defaults to `zh_female_vv_uranus_bigtts`
- `VOLC_TTS_FORMAT`: defaults to `mp3`
- `VOLC_TTS_SAMPLE_RATE`: defaults to `24000`

## Usage

```bash
python3 {baseDir}/scripts/volc_tts.py "欢迎使用 OpenClaw"
python3 {baseDir}/scripts/volc_tts.py "今天心情不错" --voice zh_female_vv_uranus_bigtts --output ./speech.mp3
python3 {baseDir}/scripts/volc_tts.py "Hello from Ark" --language en --format mp3
```

## Output

The script prints JSON:

```json
{
  "success": true,
  "type": "audio",
  "local_path": "outputs/tts/tts_20260615_120000.mp3",
  "format": "mp3",
  "bytes": 12345,
  "speaker": "zh_female_vv_uranus_bigtts",
  "sample_rate": 24000,
  "resource_id": "seed-tts-2.0"
}
```

## Failure Reporting

Report:

- Missing API key variable names.
- HTTP status and provider message.
- Empty audio stream.
- Local file write failure path.
