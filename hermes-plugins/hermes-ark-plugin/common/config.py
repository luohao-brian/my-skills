"""Configuration helpers for the Hermes Ark plugin."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

PLUGIN_ID = "ark"
DEFAULT_BACKEND = "ark-agent-plan"
BACKENDS = {
    "ark-agent-plan": {
        "base_url": "https://ark.cn-beijing.volces.com/api/plan/v3",
        "api_key_env": "ARK_AGENT_PLAN_API_KEY",
        "tts_url": "https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional",
        "stt_url": "wss://openspeech.bytedance.com/api/v3/plan/sauc/bigmodel_nostream",
        "speech_api_key_env": "ARK_AGENT_PLAN_API_KEY",
    },
    "ark-api": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key_env": "ARK_API_KEY",
        "tts_url": "https://openspeech.bytedance.com/api/v3/tts/unidirectional",
        "stt_url": "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_nostream",
        "speech_api_key_env": "ARK_TTS_X_API_KEY",
    },
}
_PLUGIN_CONTEXT: Any = None


def configure_context(ctx: Any) -> None:
    global _PLUGIN_CONTEXT
    _PLUGIN_CONTEXT = ctx


def load_plugin_config() -> dict[str, Any]:
    """Return `plugins.entries.ark` from Hermes config."""
    try:
        from hermes_cli.config import load_config
    except Exception:
        return {}
    config = load_config() or {}
    plugins = config.get("plugins")
    if not isinstance(plugins, dict):
        return {}
    entries = plugins.get("entries")
    if not isinstance(entries, dict):
        return {}
    entry = entries.get(PLUGIN_ID)
    if not isinstance(entry, dict):
        return {}
    settings = entry.get("settings")
    if isinstance(settings, dict):
        # Canonical v2 location wins while old root keys remain readable.
        return {**entry, **settings}
    return entry


def dotenv_value(name: str) -> str:
    hermes_home = Path(os.getenv("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
    for env_path in (Path.cwd() / ".env", hermes_home / ".env"):
        try:
            lines = env_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == name:
                return value.strip().strip('"').strip("'")
    return ""


def env_value(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    return dotenv_value(name)


def resolve_secret(value: str) -> str:
    """Resolve `${ENV}` references while leaving plain values intact."""
    if not isinstance(value, str):
        return ""
    raw = value.strip()
    if raw.startswith("${") and raw.endswith("}"):
        return env_value(raw[2:-1])
    return raw


def api_key() -> str:
    return section_api_key("ark")


def section_backend(name: str) -> str:
    value = str(section(name).get("backend") or DEFAULT_BACKEND).strip()
    return value if value in BACKENDS else DEFAULT_BACKEND


def section_api_key(name: str, *, speech: bool = False) -> str:
    """Resolve the selected backend's credential without cross-backend fallback."""
    cfg = section(name)
    value = resolve_secret(str(cfg.get("api_key", "")))
    if value:
        return value
    backend = section_backend(name)
    env_name = BACKENDS[backend]["speech_api_key_env" if speech else "api_key_env"]
    value = env_value(env_name)
    if value:
        return value
    # One-release compatibility for old Agent Plan root config only.
    if backend == DEFAULT_BACKEND:
        legacy = resolve_secret(str(load_plugin_config().get("api_key", "")))
        if legacy:
            return legacy
    return ""


def section(name: str) -> dict[str, Any]:
    if _PLUGIN_CONTEXT is not None:
        try:
            value = _PLUGIN_CONTEXT.get_config(name, {})
            if isinstance(value, dict):
                return value
        except Exception:
            pass
    cfg = load_plugin_config()
    value = cfg.get(name)
    return value if isinstance(value, dict) else {}


def ark_base_url(name: str = "ark") -> str:
    configured = resolve_secret(str(section(name).get("base_url") or ""))
    return configured or BACKENDS[section_backend(name)]["base_url"]


def speech_endpoint(name: str, kind: str) -> str:
    configured = resolve_secret(str(section(name).get("base_url") or ""))
    if configured:
        return configured
    key = "tts_url" if kind == "tts" else "stt_url"
    return BACKENDS[section_backend(name)][key]


def timeout_seconds(name: str, default: float) -> float:
    raw = section(name).get("timeout_seconds", default)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default
