---
name: ark-tts
description: 使用 Ark Agent Plan（默认）或 Ark API 的豆包语音接口把文本生成音频。适用于播报、旁白、配音草稿、语音接口验证和需要返回本地音频路径的任务。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-tts
metadata: {"openclaw":{"skillKey":"ark-tts","emoji":"🔊","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-tts","requires":{"anyBins":["python3","python"]},"primaryEnv":"ARK_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# Ark TTS

Synthesize speech with Volcengine Ark and save the audio locally.

## Optional Reads

- Read [references/ark-tts.md](references/ark-tts.md) for backend, output, or failure details.
- Read [references/seed-tts-2.0-voices.md](references/seed-tts-2.0-voices.md) when choosing or changing a voice.
- Read `scripts/volc_tts.py --help` only when you need exact current flags.

## Command

```bash
python3 {baseDir}/scripts/volc_tts.py "要合成的文本" --output ./outputs/tts.mp3
```

If `python3` is unavailable, use `python`.

## Contract

1. Use Agent Plan by default. Map explicit user wording `ARK-API` or `方舟 API` to `--backend ark-api`; map `ARK-AGENT-PLAN` or `方舟 Agent Plan` to `--backend ark-agent-plan`. Never switch or retry across backends automatically. Both backends use the same `seed-tts-2.0` voice catalog.
2. Write the audio file to the requested output path, or to `./outputs/tts/` when no path is supplied.
3. When Ark returns subtitle/timestamp events, write a sibling `.transcript.json` timeline next to the audio file.
4. Expect stdout JSON containing `success`, `backend`, `resource_id`, `local_path`, `transcript_path`, `transcript_segments`, `format`, `bytes`, `speaker`, and `sample_rate`.
5. Treat credential, resource id, endpoint, or network failures as failed skill calls and surface the exact missing variable or API error.

## Defaults

- Endpoint: selected by `--backend`; see [references/ark-tts.md](references/ark-tts.md).
- Resource id: fixed `seed-tts-2.0`.
- Speaker: `zh_female_vv_uranus_bigtts` unless `--voice` selects another documented 2.0 voice.
- Output format: `mp3`.

Use CLI flags for backend, output, voice, format, sample rate, speed, language,
and emotion. The script reads no Agent-specific config file.
