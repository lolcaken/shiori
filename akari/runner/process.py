"""Run ONE DownloadPlan as a subprocess.

Stdio is inherited so the user watches yt-dlp's own progress output.
The argv is always a list — never a shell string — so ``&`` or ``;``
in a video title cannot break out of the command.
"""
from __future__ import annotations

import subprocess
import time

from akari.core.models import DownloadPlan, TabOutcome


def run_plan(plan: DownloadPlan) -> TabOutcome:
    start = time.monotonic()
    completed = subprocess.run(plan.argv)
    return TabOutcome(
        plan=plan, returncode=completed.returncode, elapsed=time.monotonic() - start
    )
