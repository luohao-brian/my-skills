---
name: ark-seed-audio
description: 使用 Ark API 的豆包 Seed Audio 1.0 接口把文本生成音效、多人对白或完整场景音频。适用于拟音、环境声、角色互动和音频场景创作。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-seed-audio
metadata: {"openclaw":{"skillKey":"ark-seed-audio","emoji":"🎧","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-seed-audio","primaryEnv":"ARK_SEED_AUDIO_API_KEY","requires":{"bins":["python3"],"env":["ARK_SEED_AUDIO_API_KEY"]}}}
---

# Ark Seed Audio

Generate sound effects, dialogue, or a complete audio scene with Seed Audio 1.0 and save the audio locally.

## Optional Reads

- Read [references/usage.md](references/usage.md) for credentials, output, prompt examples, or failures.
- Read [references/preset-voices.json](references/preset-voices.json) or use `--list-voices` when choosing a preset voice. This catalog matches the Ark TTS 2.0 preset list.
- Read `scripts/seed_audio.py --help` only when exact flags are needed.

## Command

```bash
python3 {baseDir}/scripts/seed_audio.py --prompt-file ./scene.txt --output "$HOME/Documents/agent-workspace/scene.mp3"
```

For speech, add `--voice <voice_id>` once per character in prompt order. Refer to them as `@音频1`, `@音频2` in the prompt.

## Contract

1. Use the Ark API audio-generation endpoint with `ARK_SEED_AUDIO_API_KEY`. Agent Plan support for this model is not established; do not switch credentials or endpoints.
2. For sound effects without speech, describe the sound source, action, distance, space, duration, and timing. Omit `--voice`.
3. Select speech voices from the same Seed TTS 2.0 preset catalog used by `ark-tts`. For multi-character audio, put exact lines, role, delivery, and approximate cue times in the prompt. List `--voice` values in the same order as their `@音频N` labels.
4. Save the returned audio to the requested path, or under `$HOME/Documents/agent-workspace/ark-seed-audio/` by default. Save returned subtitles as a sibling `.subtitle.json` when present. Report the local audio path and any provider error.
5. Treat prompt timing and duration as generation controls, not frame-exact guarantees. Listen to the result before asserting that a requested sound, emotion, or cue was achieved.

## Defaults

- Model: `seed-audio-1.0` through Ark API.
- Voice: none for sound effects; choose documented presets with `--voice` for speech.
- Output format: `mp3`.
