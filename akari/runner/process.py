"""Run ONE DownloadPlan as a subprocess with organized live logging.

yt-dlp's stdout is streamed (never inherited raw): progress spam collapses
into a single in-place status line, each finished video becomes exactly one
``ok`` line (merged parts and subtitle sidecars stay silent), skips become
one ``skip`` line, and ERROR lines always surface. ``--verbose`` bypasses
all of this and prints yt-dlp raw.

The argv is always a list — never a shell string — so ``&`` or ``;``
in a video title cannot break out of the command.
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

from akari.core.models import DownloadPlan, TabOutcome
from akari.runner.progress import (
    ErrorLine,
    FileStart,
    MergeStart,
    Progress,
    Skipped,
    WarningLine,
    parse_line,
)

_SUBTITLE_EXTENSIONS = frozenset(
    {".vtt", ".srt", ".ass", ".lrc", ".ttml", ".srv1", ".srv2", ".srv3", ".json3"}
)
_FORMAT_PART = re.compile(r"\.f\d+\.[A-Za-z0-9]+$")


def _kind_of(filename: str) -> str:
    """Classify a destination file: a final video, a merge part, or a sidecar."""
    if Path(filename).suffix.lower() in _SUBTITLE_EXTENSIONS:
        return "sidecar"
    if _FORMAT_PART.search(filename):
        return "part"
    return "video"


def run_plan(plan: DownloadPlan, verbose: bool = False) -> TabOutcome:
    start = time.monotonic()
    proc = subprocess.Popen(
        plan.argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    errors = 0
    warnings = 0
    current: str | None = None
    current_kind = "video"
    in_parts = False
    video_start = start
    live = sys.stdout.isatty() and not verbose
    status_width = 0

    def show_status(text: str) -> None:
        nonlocal status_width
        if not live:
            return
        status_width = max(status_width, len(text))
        sys.stdout.write("\r" + text.ljust(status_width))
        sys.stdout.flush()

    def show_line(text: str) -> None:
        if live and status_width:
            sys.stdout.write("\r" + " " * status_width + "\r")
        print(text, flush=True)

    assert proc.stdout is not None
    for raw in proc.stdout:
        line = raw.rstrip("\n")
        if verbose:
            print(line, flush=True)
            continue
        event = parse_line(line)
        if isinstance(event, FileStart):
            current = Path(event.path).name
            current_kind = _kind_of(current)
            if current_kind == "video":
                video_start = time.monotonic()
                in_parts = False
            elif current_kind == "part" and not in_parts:
                video_start = time.monotonic()
                in_parts = True
            # Sidecars never touch the video clock.
        elif isinstance(event, MergeStart):
            show_line(
                f"  ok {Path(event.path).name} ({time.monotonic() - video_start:.1f}s)"
            )
            current = None
            in_parts = False
        elif isinstance(event, Progress):
            if event.done:
                if current_kind == "video" and current is not None:
                    size = f" ({event.total}" if event.total else " ("
                    show_line(
                        f"  ok {current}"
                        f"{size}, {time.monotonic() - video_start:.1f}s)"
                    )
                    in_parts = False
                # Parts and sidecars stay silent: the MergeStart line
                # reports a merged video; sidecars need no report.
                current = None
            else:
                show_status(f"  dl {event.describe()} -- {current or ''}".rstrip())
        elif isinstance(event, Skipped):
            show_line(f"  skip {Path(event.path).name} (already archived)")
            current = None
        elif isinstance(event, ErrorLine):
            errors += 1
            show_line(f"  ERROR: {event.text}")
        elif isinstance(event, WarningLine):
            warnings += 1
        # Ignored (extraction chatter, postprocessor notes) stays silent.

    proc.wait()
    if live and status_width:
        sys.stdout.write("\n")
    return TabOutcome(
        plan=plan,
        returncode=proc.returncode,
        elapsed=time.monotonic() - start,
        errors=errors,
        warnings=warnings,
    )
