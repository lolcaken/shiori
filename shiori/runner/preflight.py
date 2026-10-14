"""Verify the external tools shiori shells out to are present and runnable."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

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


def check_disk_space(path: Path, min_gb: float) -> None:
    """Refuse to start when the output drive holds less than min_gb free."""
    anchor = Path(path).expanduser()
    anchor = anchor if anchor.is_absolute() else Path.cwd() / anchor
    root = anchor.anchor or Path.cwd().anchor
    free_gb = shutil.disk_usage(str(root)).free / 1024**3
    if free_gb < min_gb:
        raise PreflightError(
            f"only {free_gb:.1f} GiB free on {root} "
            f"(need at least {min_gb:g} GiB; see --min-disk-gb)"
        )
