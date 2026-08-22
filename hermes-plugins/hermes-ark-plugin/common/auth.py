"""Authentication helpers for Ark API calls."""

from __future__ import annotations

from .config import section_api_key


def require_api_key(section: str = "ark", *, speech: bool = False) -> str:
    key = section_api_key(section, speech=speech)
    if not key:
        from .config import BACKENDS, section_backend
        backend = section_backend(section)
        env_name = BACKENDS[backend]["speech_api_key_env" if speech else "api_key_env"]
        raise RuntimeError(f"{env_name} is not configured for backend {backend}")
    return key
