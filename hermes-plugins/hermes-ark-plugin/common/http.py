"""HTTP helpers for Ark API calls."""

from __future__ import annotations

from typing import Any


def ark_headers(api_key: str, resource_id: str | None = None) -> dict[str, Any]:
    headers: dict[str, Any] = {"Authorization": f"Bearer {api_key}"}
    if resource_id:
        headers["X-Api-Resource-Id"] = resource_id
    return headers

