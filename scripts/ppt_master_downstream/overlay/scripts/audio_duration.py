"""Read audio duration without depending on one platform-specific command."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import wave
from pathlib import Path


def _ffprobe_duration(path: Path) -> float | None:
    if shutil.which("ffprobe") is None:
        return None
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "json", str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return None
        duration = float(json.loads(result.stdout or "{}").get("format", {}).get("duration", 0))
        return duration if duration > 0 else None
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired):
        return None


def _wave_duration(path: Path) -> float | None:
    if path.suffix.lower() != ".wav":
        return None
    try:
        with wave.open(str(path), "rb") as audio:
            rate = audio.getframerate()
            return audio.getnframes() / rate if rate > 0 else None
    except (OSError, wave.Error):
        return None


def _afinfo_duration(path: Path) -> float | None:
    if shutil.which("afinfo") is None:
        return None
    try:
        result = subprocess.run(
            ["afinfo", str(path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    match = re.search(r"estimated duration:\s*([0-9.]+)\s*sec", result.stdout)
    if not match:
        return None
    duration = float(match.group(1))
    return duration if duration > 0 else None


def probe_audio_duration(path: Path) -> float | None:
    """Return a positive duration using ffprobe, WAV metadata, or afinfo."""
    if not path.is_file() or path.stat().st_size == 0:
        return None
    return _ffprobe_duration(path) or _wave_duration(path) or _afinfo_duration(path)
