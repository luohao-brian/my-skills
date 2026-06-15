---
name: stt
description: 使用火山引擎 Ark 语音识别接口把本地音频转成文字。适用于录音转写、字幕初稿、会议音频识别、语音消息解析和 STT 接口验证。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/stt
metadata: {"openclaw":{"skillKey":"stt","emoji":"🎧","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/stt","requires":{"anyBins":["python3","python"],"env":["VOLC_AGENT_PLAN_API_KEY"]},"primaryEnv":"VOLC_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"websocket-client>=1.7,<2"}]}}
---

# Volcengine Ark STT

Use this skill to transcribe local audio through Volcengine Ark speech recognition.

## Required Reads

- Read [references/ark-stt.md](references/ark-stt.md) before transcribing.
- Read `scripts/volc_stt.py --help` only when exact flags are needed.

## Command

```bash
python3 {baseDir}/scripts/volc_stt.py ./audio.wav
```

## Contract

1. Require `VOLC_AGENT_PLAN_API_KEY`; compatibility fallbacks are accepted by the script.
2. Accept local audio files only. Do not invent remote downloads inside the skill.
3. Return JSON containing `success`, `transcript`, `audio_path`, and the final provider payload.
4. If the transcript is empty, report that as a failure instead of guessing content.
