"""Bytes downloaded, measured from disk — no output parsing involved.

After a tab finishes, everything in its folder with a modification time
newer than the tab's start is data this run wrote. That covers fresh
downloads and `--full` overwrites alike, while untouched files
(already archived) are excluded.
"""
from __future__ import annotations

from pathlib import Path


def format_bytes(n: int) -> str:
    """Human size in yt-dlp's units (B, KiB, MiB, GiB, …)."""
    size = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TiB"  # unreachable, keeps type checkers calm


def downloaded_since(directory: Path, since: float) -> tuple[int, int]:
    """Return (file count, total bytes) written in directory since timestamp."""
    if not directory.is_dir():
        return (0, 0)
    # One second of grace: on Windows the filesystem clock can tick coarser
    # than time.time(), stamping a just-written file slightly *before* now.
    cutoff = since - 1.0
    count, total = 0, 0
    for path in directory.rglob("*"):
        if path.is_file() and path.stat().st_mtime >= cutoff:
            count += 1
            total += path.stat().st_size
    return (count, total)
