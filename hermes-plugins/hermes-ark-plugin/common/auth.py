"""Authentication helpers for Ark API calls."""

from __future__ import annotations

from .config import api_key


def require_api_key() -> str:
    key = api_key()
    if not key:
        raise RuntimeError("VOLC_AGENT_PLAN_API_KEY is not configured")
    return key
