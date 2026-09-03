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
- Use the selected upstream route's browser requirements and verification
  procedure. Report an unavailable required browser at the affected stage.

## Image generation and search

Follow the upstream acquisition path, image workflow, and manifests. For API
generation, select the caller-configured service through `IMAGE_BACKEND` or
`image_gen.py --backend`; the command-line option takes precedence. Agent Plan
is available as `ark-agent-plan` alongside the upstream backends. Read
[`runtime-media.md`](runtime-media.md) when using it.

## TTS

Use upstream `notes_to_audio.py` and its per-slide audio/manifest contract.
Select the service with `--provider` or the optional `TTS_PROVIDER` environment
variable; the command-line option takes precedence. Without either setting,
the upstream `edge` default applies. Agent Plan is available as
`ark-agent-plan`; read [`runtime-media.md`](runtime-media.md) when using it.
