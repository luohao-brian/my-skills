---
name: tts
description: 使用火山引擎 Ark 语音合成接口把文本生成音频文件。适用于文本转语音、播报、旁白、配音草稿、语音接口验证和需要返回本地音频路径的任务。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/tts
metadata: {"openclaw":{"skillKey":"tts","emoji":"🔊","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/tts","requires":{"anyBins":["python3","python"],"env":["ARK_AGENT_PLAN_API_KEY"]},"primaryEnv":"ARK_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# Volcengine Ark TTS

Use this skill to synthesize speech with Volcengine Ark. Keep the main context small: read only the files needed for the requested operation.

## Required Reads

- Read [references/ark-tts.md](references/ark-tts.md) before running synthesis.
- Read `scripts/volc_tts.py --help` only when you need exact current flags.

## Command

```bash
python3 {baseDir}/scripts/volc_tts.py "要合成的文本" --output ./outputs/tts.mp3
```

If `python3` is unavailable, use `python`.

## Contract

1. Require `ARK_AGENT_PLAN_API_KEY`; the script does not read any other API key variable.
2. Write the audio file to the requested output path, or to `./outputs/tts/` when no path is supplied.
3. When Ark returns subtitle/timestamp events, write a sibling `.transcript.json` timeline next to the audio file.
4. Return JSON containing `success`, `local_path`, `transcript_path`, `transcript_segments`, `format`, `bytes`, `speaker`, and request metadata.
5. If credentials, resource id, endpoint, or network access fail, report the exact missing variable or API error.

## Defaults

- Endpoint: Ark plan TTS endpoint from Hermes Ark plugin; no `appid` is used.
- Resource id: `seed-tts-2.0`.
- Speaker: Hermes Ark plugin `text_to_speech.voice` when configured.
- Output format: `mp3`.
