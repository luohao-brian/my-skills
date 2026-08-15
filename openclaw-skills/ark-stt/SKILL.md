---
name: ark-stt
description: 使用 Ark Agent Plan（默认）或 Ark API 的豆包语音接口把本地 16 kHz 音频转成文字。适用于录音转写、字幕初稿、会议音频和语音消息解析。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-stt
metadata: {"openclaw":{"skillKey":"ark-stt","emoji":"🎧","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-stt","requires":{"anyBins":["python3","python"]},"primaryEnv":"ARK_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"websocket-client>=1.7,<2"}]}}
---

# Ark STT

Use this skill to transcribe local audio through Volcengine Ark speech recognition.

## Optional Reads

- Read [references/ark-stt.md](references/ark-stt.md) for backend details, audio constraints, or failures.
- Read `scripts/volc_stt.py --help` only when exact flags are needed.

## Command

```bash
python3 {baseDir}/scripts/volc_stt.py ./audio.wav
```

## Contract

1. Use Agent Plan by default. Map explicit user wording `ARK-API` or `方舟 API` to `--backend ark-api`; map `ARK-AGENT-PLAN` or `方舟 Agent Plan` to `--backend ark-agent-plan`. Never switch or retry across backends automatically. See [references/ark-stt.md](references/ark-stt.md) for credentials and endpoints.
2. Accept local audio files only. Do not invent remote downloads inside the skill.
3. Require the provider-supported 16 kHz input contract, derive duration from the input format, and send approximately 100-200 ms per audio package while receiving responses concurrently.
4. Expect concise stdout JSON containing `success`, `backend`, `transcript`, `audio_path`, and `duration_ms`; use `--raw` only when exact provider fields are needed.
5. Treat an empty transcript as a failed skill call.
