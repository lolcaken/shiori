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

from shiori.core.models import DownloadPlan, TabOutcome
from shiori.runner.highlight import colorize_progress, enable_vt, use_color
from shiori.runner.progress import (
    ErrorLine,
    FileStart,
    MergeStart,
    Progress,
    RemuxStart,
    Skipped,
    WarningLine,
    parse_line,
)

_SUBTITLE_EXTENSIONS = frozenset(
    {".vtt", ".srt", ".ass", ".lrc", ".ttml", ".srv1", ".srv2", ".srv3", ".json3"}
)
_IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})
# Containers --remux-video may still rewrite into the final .mp4.
_INTERMEDIATE_EXTENSIONS = frozenset({".mkv", ".webm", ".mov", ".avi", ".flv", ".ts"})
_FORMAT_PART = re.compile(r"\.f\d+\.[A-Za-z0-9]+$")


def _kind_of(filename: str) -> str:
    """Classify a destination file: final video, merge/remux part, or sidecar."""
    suffix = Path(filename).suffix.lower()
    if suffix in _SUBTITLE_EXTENSIONS or suffix in _IMAGE_EXTENSIONS:
        return "sidecar"
    if suffix in _INTERMEDIATE_EXTENSIONS or _FORMAT_PART.search(filename):
        return "part"
    return "video"


def run_plan(plan: DownloadPlan, verbose: bool = False, no_color: bool = False) -> TabOutcome:
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
    skipped = 0
    current: str | None = None
    current_kind = "video"
    in_parts = False
    video_start = start
    reported: set[str] = set()
    live = sys.stdout.isatty() and not verbose
    colored = live and use_color(no_color)
    if colored:
        enable_vt()
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

    def report_ok(name: str, detail: str) -> None:
        """Print one ok line per final file; never report a path twice."""
        if name in reported:
            return
        reported.add(name)
        show_line(f"  ok {name} ({detail})")

    assert proc.stdout is not None
    for raw in proc.stdout:
        line = raw.rstrip("\n")
        if verbose:
            event = parse_line(line)
            if isinstance(event, Skipped):
                skipped += 1
            elif isinstance(event, ErrorLine):
                errors += 1
            elif isinstance(event, WarningLine):
                warnings += 1
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
        elif isinstance(event, (MergeStart, RemuxStart)):
            report_ok(
                Path(event.path).name, f"{time.monotonic() - video_start:.1f}s"
            )
            current = None
            in_parts = False
        elif isinstance(event, Progress):
            if event.done:
                if current_kind == "video" and current is not None:
                    size = f"{event.total}, " if event.total else ""
                    report_ok(
                        current,
                        f"{size}{time.monotonic() - video_start:.1f}s",
                    )
                    in_parts = False
                # Parts and sidecars stay silent: the MergeStart/RemuxStart
                # line reports a merged video; sidecars need no report.
                current = None
            else:
                if colored:
                    print(colorize_progress(event, current or ""), flush=True)
                else:
                    status = f"  dl {event.describe()} -- {current or ''}".rstrip()
                    if skipped:
                        status += f" ({skipped} archived)"
                    show_status(status)
        elif isinstance(event, Skipped):
            skipped += 1
            downloading = current is not None and current_kind in ("video", "part")
            current = None
            if live and not downloading:
                show_status(f"  -- {skipped} archived")
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
        skipped=skipped,
    )
