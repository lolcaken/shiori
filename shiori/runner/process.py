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


def run_plan(plan: DownloadPlan) -> TabOutcome:
    start = time.monotonic()
    completed = subprocess.run(plan.argv)
    return TabOutcome(
        plan=plan, returncode=completed.returncode, elapsed=time.monotonic() - start
    )
