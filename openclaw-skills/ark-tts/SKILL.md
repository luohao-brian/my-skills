---
name: ark-tts
description: 使用 Ark Agent Plan 语音合成接口把文本生成音频文件。适用于文本转语音、播报、旁白、配音草稿、语音接口验证和需要返回本地音频路径的任务。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-tts
metadata: {"openclaw":{"skillKey":"ark-tts","emoji":"🔊","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-tts","requires":{"anyBins":["python3","python"],"env":["ARK_AGENT_PLAN_API_KEY"]},"primaryEnv":"ARK_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# Ark Agent Plan TTS

Use this skill to synthesize speech with Volcengine Ark. Keep the main context small: read only the files needed for the requested operation.

## Required Reads

- Read [references/ark-tts.md](references/ark-tts.md) before running synthesis.
- Read [references/seed-tts-2.0-voices.md](references/seed-tts-2.0-voices.md) when choosing or changing a voice.
- Read `scripts/volc_tts.py --help` only when you need exact current flags.

## Command

```bash
python3 {baseDir}/scripts/volc_tts.py "要合成的文本" --output ./outputs/tts.mp3
```

If `python3` is unavailable, use `python`.

## Contract

1. The script reads only `ARK_AGENT_PLAN_API_KEY` and uses the fixed Agent Plan endpoint and `seed-tts-2.0` resource.
2. Write the audio file to the requested output path, or to `./outputs/tts/` when no path is supplied.
3. When Ark returns subtitle/timestamp events, write a sibling `.transcript.json` timeline next to the audio file.
4. Expect stdout JSON containing `success`, `local_path`, `transcript_path`, `transcript_segments`, `format`, `bytes`, `speaker`, and `sample_rate`.
5. Treat credential, resource id, endpoint, or network failures as failed skill calls and surface the exact missing variable or API error.

## Defaults

- Endpoint: Ark Agent Plan TTS endpoint.
- Resource id: fixed `seed-tts-2.0`.
- Speaker: `zh_female_vv_uranus_bigtts` unless `--voice` selects another documented 2.0 voice.
- Output format: `mp3`.

Use CLI flags only for output, voice, format, and sample rate. The script reads no Agent-specific config file.
