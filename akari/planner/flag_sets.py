"""yt-dlp argv fragments, grouped by concern so each can be tested alone."""
from __future__ import annotations

from pathlib import Path


def format_flags() -> list[str]:
    return ["-t", "mp4"]


def subtitle_flags(sub_langs: str) -> list[str]:
    return [
        "--write-subs",
        "--write-auto-subs",
        "--embed-subs",
        "--sub-langs", sub_langs,
    ]


def subtitle_output_flags(subtitle_dir: Path) -> list[str]:
    """Point subtitle files at an EXACT template inside the scratch dir.

    A bare ``--paths subtitle:…`` only prepends to the video's ``-o``
    directory, which leaks .vtt files next to the mp4 when ``-o`` holds
    an absolute path. An explicit ``-o subtitle:…`` template replaces
    the location outright, so the archive folder stays mp4-only and the
    scratch dir (deleted after the run) holds the intermediates.
    """
    return ["-o", f"subtitle:{subtitle_dir.as_posix()}/%(title)s.%(ext)s"]


def resume_flags(archive_path: Path, full: bool) -> list[str]:
    flags = ["--continue", "--no-overwrites", "--ignore-errors"]
    if not full:
        flags += ["--download-archive", str(archive_path)]
    return flags


def network_flags(jobs: int, sleep_interval: float) -> list[str]:
    return ["-N", str(jobs), "--sleep-interval", str(sleep_interval)]


def filesystem_flags() -> list[str]:
    return ["--trim-filenames", "180", "--windows-filenames"]


def metadata_flags() -> list[str]:
    return ["--embed-metadata", "--embed-thumbnail"]


def date_flags(since: str | None, until: str | None) -> list[str]:
    flags: list[str] = []
    if since:
        flags += ["--dateafter", since]
    if until:
        flags += ["--datebefore", until]
    return flags
