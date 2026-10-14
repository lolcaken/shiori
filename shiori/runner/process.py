"""Run ONE DownloadPlan as a subprocess.

yt-dlp's output passes straight through to the terminal, exactly as
yt-dlp emits it (its own in-place progress, warnings and errors).
The argv is always a list — never a shell string — so ``&`` or ``;``
in a video title cannot break out of the command.
"""
from __future__ import annotations

import subprocess
import time

from shiori.core.models import DownloadPlan, TabOutcome


def run_argv(argv: list[str]) -> int:
    """Run one command with inherited stdio; return its exit code."""
    return subprocess.run(argv).returncode


def run_plan(plan: DownloadPlan) -> TabOutcome:
    start = time.monotonic()
    returncode = run_argv(plan.argv)
    return TabOutcome(
        plan=plan, returncode=returncode, elapsed=time.monotonic() - start
    )
