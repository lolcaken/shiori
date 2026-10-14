"""Verify the external tools shiori shells out to are present and runnable."""
from __future__ import annotations

import shutil
import subprocess

from shiori.core.errors import PreflightError


def find_binary(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise PreflightError(
            f"required tool {name!r} was not found on PATH; "
            f"install it and re-run"
        )
    return path


def tool_version(binary: str, version_args: list[str]) -> str:
    try:
        completed = subprocess.run(
            [binary, *version_args],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PreflightError(f"could not run {binary!r}: {exc}") from exc
    if completed.returncode != 0:
        raise PreflightError(f"{binary!r} failed its version check")
    return (completed.stdout or completed.stderr).strip().splitlines()[0]


def preflight(yt_dlp: str) -> dict[str, str]:
    """Return ``{tool: version}`` or raise PreflightError.

    yt-dlp does the downloading; ffmpeg is mandatory because merging
    formats and embedding soft subtitles both go through it.
    """
    return {
        "yt-dlp": tool_version(find_binary(yt_dlp), ["--version"]),
        "ffmpeg": tool_version(find_binary("ffmpeg"), ["-version"]),
    }
