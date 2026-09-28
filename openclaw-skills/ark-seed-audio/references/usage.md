# Seed Audio 1.0 usage

Official model description: https://seed.bytedance.com/zh/blog/from-speech-to-audio-creation-introducing-the-seed-audio-1-0-audio-creation-model

Official audio-generation HTTP API: https://docs.volcengine.com/docs/6561/2550782?lang=zh

The model jointly generates speech, sound effects, and ambience. A prompt can request an isolated sound effect or an entire mixed scene. The endpoint is `POST https://openspeech.bytedance.com/api/v3/tts/create` with `X-Api-Key`; the model ID is `seed-audio-1.0`.

## Dependencies and preset voice IDs

- Runtime: `python3` and a Seed Audio-enabled Ark API key in `ARK_SEED_AUDIO_API_KEY`. The skill reads this variable exclusively and does not call Agent Plan. A login Bash shell loads an export in `$HOME/.bash_profile`; other agent processes must inherit the variable from their launcher environment.
- Find a voice by its display name, scenario, or ID without an API key:

  ```bash
  python3 {baseDir}/scripts/seed_audio.py --list-voices 云舟
  ```

  The JSON result contains `name`, `id`, `scenario`, and `language`. Copy its exact `id` into `--voice`; repeat the option in character order. The bundled [preset-voices.json](preset-voices.json) mirrors the [Seed TTS 2.0 voice catalog](../../ark-tts/references/seed-tts-2.0-voices.md) used by `ark-tts`; its header links to the official voice list. The Ark protocol test checks that the two catalogs have identical IDs. The script rejects IDs absent from this catalog; choose a listed preset or surface the missing ID for a catalog refresh.
- A catalog entry confirms that the ID is a documented TTS preset, not that this account can use it with Seed Audio. A successful generation call confirms protocol access. Listen to the audio to check whether the intended character voice was actually produced. The output JSON records `voices` in `@音频N` order. `ark-stt` performs recognition and has no voice selection.

## Sound effect only

```bash
python3 {baseDir}/scripts/seed_audio.py \
  "8秒音效：空旷地下停车场，一串沉重脚步从远处逐渐靠近，短暂停顿后金属门猛地关上。无台词、无人声、无音乐。" \
  --output "$HOME/Documents/agent-workspace/parking-sfx.mp3"
```

## Multi-character scene

Write a UTF-8 prompt file with the entire scene and exact dialogue. For example:

```text
约25秒的雨夜站台场景。细雨持续，脚步声从远处靠近，无音乐。对白清楚，环境声不要盖住对白。
约4秒，女声参考@音频1，紧张地说：“你听见了吗？”
约10秒，男声参考@音频2，低声说：“先别回头。”
```

```bash
python3 {baseDir}/scripts/seed_audio.py --prompt-file ./scene.txt \
  --voice zh_female_vv_uranus_bigtts \
  --voice zh_male_m191_uranus_bigtts \
  --output "$HOME/Documents/agent-workspace/station.mp3"
```

Each `--voice` occupies one `@音频N` slot in the order given. For two or three voices, the prompt must name every corresponding `@音频N` (or `@AudioN`) label. A single voice may omit the label. This skill accepts preset voice IDs only; describe each role and delivery in the prompt as well.

| Preset | Voice ID | Seed Audio trial |
| --- | --- | --- |
| Vivi 2.0 | `zh_female_vv_uranus_bigtts` | Succeeded in a two-character scene |
| 云舟 2.0 | `zh_male_m191_uranus_bigtts` | Succeeded in a two-character scene |

## Output and options

The command defaults to MP3 at 48 kHz. `--format` accepts `mp3`, `wav`, `pcm`, or `ogg_opus`; `--sample-rate` accepts 8000, 16000, 24000, 32000, 44100, or 48000. It prints JSON with `success`, `model`, `local_path`, `subtitle_path`, `duration`, `original_duration`, `format`, `sample_rate`, `voices`, and `bytes`.

`--prompt-file` keeps long scripts out of shell quoting. `--voice` can be repeated up to three times. `--timeout` sets the request timeout in seconds. Do not place the API key in the prompt, command line, or output files.
