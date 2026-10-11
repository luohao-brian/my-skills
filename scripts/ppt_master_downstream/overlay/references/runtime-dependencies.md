# Dependency and Capability Contract

The calling runtime owns its Python launcher, environment, dependency manager,
browser installation, credentials, billing, and process lifecycle. This
distribution follows the upstream Volcengine image backend and adds the local
Ark Agent Plan TTS provider. Explicit provider settings take precedence.

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

Follow the upstream acquisition path, image workflow, and manifests. Use the
upstream `volcengine` backend for either Ark API or Agent Plan by setting the
complete `VOLCENGINE_BASE_URL` endpoint, the matching key variable accepted by
the upstream backend, and optional `VOLCENGINE_MODEL`. The command-line option
takes precedence. Read [`runtime-media.md`](runtime-media.md).

## TTS

Use upstream `notes_to_audio.py` and its per-slide audio/manifest contract.
Select the service with `--provider` or the optional `TTS_PROVIDER` environment
variable; the command-line option takes precedence. Without either setting,
the downstream default is `ark-agent-plan`. Read [`runtime-media.md`](runtime-media.md).
