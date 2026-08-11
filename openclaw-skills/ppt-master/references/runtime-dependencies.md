# Dependency and Capability Contract

The calling runtime owns its Python launcher, environment, dependency manager,
browser installation, model/provider selection, credentials, retries, billing,
and process lifecycle. PPT Master consumes capabilities and does not provision
or select them.

## Python and browser

- Reuse the caller-selected invocation: `python3`, `python`, `uv run python`, a
  managed virtual environment, container command, or equivalent launcher.
- Do not create, activate, delete, or relocate environments; install packages;
  alter `PATH`; switch interpreters; or download a browser unless the user
  explicitly requests environment setup or the runtime's approved dependency
  mechanism performs it.
- Check only the imports and executables required by the selected route. Report
  a missing capability and its affected stage without mutating the environment.
- Browser checks may reuse a runtime browser, installed Chrome, or
  Playwright-managed Chromium. If none is available, formal publication stops
  unless the user explicitly accepts the unverified browser stage.

## Image generation and search

Use the upstream image workflow, manifests, `image_gen.py`, Volcengine backend,
and `image_search.py` without a separate downstream image skill. API image
generation is fixed to the `ark-agent-plan` profile, its Agent Plan endpoint,
and `doubao-seedream-5.0-lite`. Read only `ARK_AGENT_PLAN_API_KEY`; ignore
`IMAGE_BACKEND`, provider bridge variables, normal Ark credentials, and legacy
Volcengine configuration. The backend is intentionally not caller-selectable.

When the confirmed acquisition path is API, invoke upstream
`image_gen.py --manifest`. When it is web, use upstream `image_search.py`. Do not
translate either path into a host-native image capability or a downstream image
manifest.

## TTS

Use upstream `notes_to_audio.py` and its per-slide audio/manifest contract. TTS
is fixed to the `ark-agent-plan` profile, the Agent Plan speech endpoint, and
`seed-tts-2.0`. Read only `ARK_AGENT_PLAN_API_KEY`; ignore `TTS_BACKEND`,
`TTS_PROVIDER`, normal Ark credentials, and legacy provider configuration. The
backend is intentionally not caller-selectable. Base URL, model, default voice,
sample rate, and output format remain internal defaults. Read
[`runtime-media.md`](runtime-media.md) for the exact execution contract.
