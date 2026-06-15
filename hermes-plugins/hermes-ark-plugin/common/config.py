"""Configuration helpers for the Hermes Ark plugin."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

PLUGIN_ID = "ark"


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
    return entry if isinstance(entry, dict) else {}


def dotenv_value(name: str) -> str:
    for env_path in (Path.cwd() / ".env", Path.home() / ".hermes/.env"):
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
    cfg = load_plugin_config()
    value = resolve_secret(str(cfg.get("api_key", "")))
    if value:
        return value
    for name in ("VOLC_AGENT_PLAN_API_KEY", "ARK_API_KEY", "OPENAPI_API_KEY"):
        value = env_value(name)
        if value:
            return value
    return ""


def section(name: str) -> dict[str, Any]:
    cfg = load_plugin_config()
    value = cfg.get(name)
    return value if isinstance(value, dict) else {}


def ark_base_url() -> str:
    return str(section("ark").get("base_url") or "https://ark.cn-beijing.volces.com/api/plan/v3")


def timeout_seconds(name: str, default: float) -> float:
    raw = section(name).get("timeout_seconds", default)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default
