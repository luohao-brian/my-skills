# Hermes Ark Plugin

Hermes v0.20.x does not natively provide direct Ark API or Ark Agent Plan
multimedia backends. This plugin keeps Hermes' built-in tool shells and adds
Ark implementations for TTS, STT, Seedream image generation, Seedance video
generation, image understanding, and video understanding.

The default backend is Ark Agent Plan. Ark API is an explicit alternative;
the plugin never crosses backends automatically when a request fails.

## What the v0.2 upgrade changes

- Uses the Hermes v2 manifest and auditable `tools.override` capability.
- Always registers Ark TTS, STT, image, and video providers. These capabilities
  remain available when understanding-tool override consent is absent.
- Keeps Hermes' native `transcribe_audio` tool, including its file guard and
  preprocessing, and only supplies the Ark STT provider behind it.
- Reuses Hermes' media resolver for image/video understanding, including
  credential-file blocking, SSRF checks, remote terminal resolution, MIME
  validation, and the 50 MB ingest limit.
- Supports both Ark Agent Plan and Ark API with backend-specific credentials,
  endpoints, models, parameters, and error messages.
- Aligns Seedream 5.0, Seedance 2.0/2.5, Seed-TTS 2.0, BigASR, and Doubao Seed
  vision contracts with the current `my-cowork` implementation.

## Install

Run from this directory in Hermes' Python environment:

```bash
python cli.py install --with-deps
```

Installation copies the plugin to `$HERMES_HOME/plugins/ark`, enables it, writes
Ark Agent Plan defaults, and selects `ark` for Hermes TTS, STT, image generation,
and video generation. Hermes then asks once for `tools.override` consent. If the
consent is declined or the install is non-interactive, the four providers still
work; Hermes keeps its native image/video understanding tools.

To configure direct Ark API instead:

```bash
python cli.py install --with-deps --backend ark-api
```

Existing installs can be reconfigured without replacing the plugin:

```bash
python cli.py config --backend ark-agent-plan
python cli.py config --backend ark-api --overwrite
```

## Credentials

| Backend/capability | Environment variable |
| --- | --- |
| Ark Agent Plan, all plugin capabilities | `ARK_AGENT_PLAN_API_KEY` |
| Ark API image/video/vision | `ARK_API_KEY` |
| Ark API TTS/STT | `ARK_TTS_X_API_KEY` |

The normal Ark speech product uses its own `X-Api-Key`; it does not use
`ARK_API_KEY`.

Seed-TTS timing fields are normalized from provider seconds to
`start_time_ms`/`end_time_ms` in the transcript sidecar.

## Configuration

Plugin-owned settings use the v2 namespace:

```yaml
plugins:
  enabled: [ark]
  entries:
    ark:
      granted_capabilities: [tools.override]
      settings:
        image_generate:
          backend: ark-agent-plan
          api_key: ${ARK_AGENT_PLAN_API_KEY}
          model: doubao-seedream-5.0-lite
          resolution: 2K
        video_generate:
          backend: ark-agent-plan
          api_key: ${ARK_AGENT_PLAN_API_KEY}
          model: doubao-seedance-2.0-fast
        vision_analyze:
          backend: ark-agent-plan
          api_key: ${ARK_AGENT_PLAN_API_KEY}
          model: doubao-seed-2.0-lite
```

The CLI writes all six sections; the excerpt only shows the main model fields.
Legacy keys directly under `plugins.entries.ark` remain readable for migration.

Provider selection remains in Hermes-owned sections:

```yaml
tts:
  provider: ark
stt:
  enabled: true
  provider: ark
image_gen:
  provider: ark
video_gen:
  provider: ark
```

## Models

- Seedream Agent Plan: `doubao-seedream-5.0-lite`
- Seedream Ark API: `doubao-seedream-5-0-260128`,
  `doubao-seedream-5-0-pro-260628`
- Seedance Agent Plan: `doubao-seedance-2.0-fast`, `doubao-seedance-2.0`
- Seedance Ark API: `doubao-seedance-2-5-260628`,
  `doubao-seedance-2-0-fast-260128`, `doubao-seedance-2-0-mini-260615`,
  `doubao-seedance-2-0-260128`
- Vision Agent Plan: `doubao-seed-2.0-lite`, `doubao-seed-2.0-mini`
- Vision Ark API: `doubao-seed-2-0-lite-260428`,
  `doubao-seed-2-0-mini-260428`

## Other commands

```bash
python cli.py status
python cli.py voices
python cli.py uninstall
python cli.py uninstall --remove-config
```

See [DESIGN.md](DESIGN.md) for ownership and degradation behavior.
