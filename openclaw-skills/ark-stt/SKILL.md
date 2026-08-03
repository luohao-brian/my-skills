---
name: ark-stt
description: 使用 Ark Agent Plan 语音识别接口把本地音频转成文字。适用于录音转写、字幕初稿、会议音频识别、语音消息解析和 STT 接口验证。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-stt
metadata: {"openclaw":{"skillKey":"ark-stt","emoji":"🎧","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-stt","requires":{"anyBins":["python3","python"],"env":["ARK_AGENT_PLAN_API_KEY"]},"primaryEnv":"ARK_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"websocket-client>=1.7,<2"}]}}
---

# Ark Agent Plan STT

Use this skill to transcribe local audio through Volcengine Ark speech recognition.

## Required Reads

- Read [references/ark-stt.md](references/ark-stt.md) before transcribing.
- Read `scripts/volc_stt.py --help` only when exact flags are needed.

## Command

```bash
python3 {baseDir}/scripts/volc_stt.py ./audio.wav
```

## Contract

1. The script reads only `ARK_AGENT_PLAN_API_KEY` and uses the fixed Agent Plan endpoint and `volc.seedasr.sauc.duration` resource.
2. Accept local audio files only. Do not invent remote downloads inside the skill.
3. Expect concise stdout JSON containing `success`, `transcript`, `audio_path`, and `duration_ms`; use `--raw` only when exact provider fields are needed.
4. Treat an empty transcript as a failed skill call.
