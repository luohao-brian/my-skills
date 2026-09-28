"""Default image route: Agent Plan, then Ark API on service failure."""

from __future__ import annotations

import re

from image_backends import backend_ark_api, backend_ark_plan


_STATUS = re.compile(r"\(([1-5][0-9]{2})\)")


def _fallback_allowed(exc: Exception) -> bool:
    """Keep malformed requests visible; fall back on service or credential failure."""
    message = str(exc).lower()
    match = _STATUS.search(message)
    status = int(match.group(1)) if match else None
    return (
        isinstance(exc, (ConnectionError, TimeoutError))
        or status in {401, 402, 403, 408, 429}
        or (status is not None and status >= 500)
        or any(token in message for token in (
            "no agent plan image key", "quota", "rate limit", "too many requests",
            "resource_exhausted", "connection", "timed out",
        ))
    )


def generate(*args, **kwargs) -> str:
    """Generate with Agent Plan, using Ark API only for an eligible failure."""
    try:
        return backend_ark_plan.generate(*args, **kwargs)
    except Exception as plan_error:
        if not _fallback_allowed(plan_error):
            raise
        print(f"Agent Plan image unavailable: {plan_error}; trying Ark API.")
        try:
            fallback_args = dict(kwargs)
            if fallback_args.get("model") in {None, backend_ark_plan.MODEL}:
                fallback_args["model"] = backend_ark_api.MODEL
            return backend_ark_api.generate(*args, **fallback_args)
        except Exception as api_error:
            raise RuntimeError(
                f"Agent Plan image failed: {plan_error}; Ark API fallback failed: {api_error}"
            ) from api_error
