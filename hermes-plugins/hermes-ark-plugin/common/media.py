"""Media encoding and validation helpers."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path


def file_to_data_url(path: str) -> str:
    p = Path(path).expanduser()
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    payload = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"

