# Hermes Ark Plugin

Unified Volcengine Ark plugin for Hermes multimodal capabilities.

This plugin is designed to live outside the Hermes core repository and be
installed into `~/.hermes/plugins/ark`. Hermes keeps the public tool names and
toolsets; this plugin owns Ark-specific provider code, API endpoints, models,
timeouts, and credentials.

Status: this repository contains the working Ark implementations for Hermes'
multimodal plugin hooks. The CLI installs, uninstalls, configures, and reports
status; the plugin registers Ark providers for generation/transcription/speech
and overrides the understanding tools.

## Install

From this repository:

```bash
python cli.py install
python cli.py config
```

The installer copies this directory to:

```text
~/.hermes/plugins/ark
```

and enables the plugin in `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - ark
```

## Configure

Default command:

```bash
python cli.py config
```

This writes the full Ark plugin block under `plugins`:

```yaml
plugins:
  enabled:
    - ark

  entries:
    ark:
      api_key: ${ARK_AGENT_PLAN_API_KEY}

      ark:
        base_url: https://ark.cn-beijing.volces.com/api/plan/v3
        timeout_seconds: 300

      text_to_speech:
        base_url: https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional
        resource_id: seed-tts-2.0
        voice: zh_female_vv_uranus_bigtts
        language: auto
        output_format: mp3
        timeout_seconds: 120
        max_text_length: 4000

      transcribe_audio:
        base_url: wss://openspeech.bytedance.com/api/v3/plan/sauc/bigmodel_nostream
        resource_id: volc.seedasr.sauc.duration
        language: zh
        output_format: txt
        timeout_seconds: 180

      image_generate:
        model: doubao-seedream-5.0-lite
        timeout_seconds: 180

      video_generate:
        model: doubao-seedance-2.0-fast
        timeout_seconds: 300
        poll_interval_seconds: 5

      vision_analyze:
        model: doubao-seed-2.0-lite
        timeout_seconds: 300
        max_tokens: 2000
        temperature: 0.1

      video_analyze:
        model: doubao-seed-2.0-lite
        timeout_seconds: 300
        max_tokens: 4000
        temperature: 0.1
        fps: 1
```

Existing unrelated plugin entries are preserved.

Use `--overwrite` if you want to replace an existing `plugins.entries.ark`
block instead of preserving user-edited values:

```bash
python cli.py config --overwrite
```

Use `--api-key-env` only when your `.env` key has a non-default name:

```bash
python cli.py config --api-key-env MY_ARK_API_KEY
```

Choose a TTS voice with a preset alias or a raw Ark speaker ID:

```bash
python cli.py voices
python cli.py config --voice vivi
python cli.py config --voice zh_male_m191_uranus_bigtts
```

The plugin reuses Hermes' existing plugin config namespace:

```yaml
plugins:
  enabled:
    - ark

  entries:
    ark:
      api_key: ${ARK_AGENT_PLAN_API_KEY}

      ark:
        base_url: https://ark.cn-beijing.volces.com/api/plan/v3
        timeout_seconds: 300

      text_to_speech:
        base_url: https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional
        resource_id: seed-tts-2.0
        voice: zh_female_vv_uranus_bigtts
        language: auto
        output_format: mp3
        timeout_seconds: 120
        max_text_length: 4000

      transcribe_audio:
        base_url: wss://openspeech.bytedance.com/api/v3/plan/sauc/bigmodel_nostream
        resource_id: volc.seedasr.sauc.duration
        language: zh
        output_format: txt
        timeout_seconds: 180

      image_generate:
        model: doubao-seedream-5.0-lite
        timeout_seconds: 180

      video_generate:
        model: doubao-seedance-2.0-fast
        timeout_seconds: 300
        poll_interval_seconds: 5

      vision_analyze:
        model: doubao-seed-2.0-lite
        timeout_seconds: 300
        max_tokens: 2000
        temperature: 0.1

      video_analyze:
        model: doubao-seed-2.0-lite
        timeout_seconds: 300
        max_tokens: 4000
        temperature: 0.1
        fps: 1
```

Provider selection stays in Hermes' native sections:

```yaml
tts:
  provider: ark

stt:
  enabled: true
  provider: ark

image_gen:
  provider: ark
  model: doubao-seedream-5.0-lite

video_gen:
  provider: ark
  model: doubao-seedance-2.0-fast
```

Store the real secret in `~/.hermes/.env`:

```bash
ARK_AGENT_PLAN_API_KEY=...
```

## Uninstall

```bash
python cli.py uninstall
```

This removes `~/.hermes/plugins/ark` and disables `ark` in
`plugins.enabled`. By default it preserves `plugins.entries.ark` so a future
reinstall can reuse the same settings.

To remove plugin config too:

```bash
python cli.py uninstall --remove-config
```

## Design

See [DESIGN.md](DESIGN.md).
