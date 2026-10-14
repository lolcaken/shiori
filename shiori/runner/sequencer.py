"""Run plans sequentially and aggregate their outcomes.

Tabs run one at a time: parallel tabs against YouTube only invite
rate limiting, and a failure in one tab must not silently cancel the rest.
"""
from __future__ import annotations

import time
from collections.abc import Callable

from shiori.core.models import DownloadPlan, RunSummary, TabOutcome
from shiori.runner.measure import downloaded_since, format_bytes
from shiori.runner.process import run_plan
from shiori.runner.reporting import format_tab_header


def run_all(
    plans: list[DownloadPlan],
    runner: Callable[[DownloadPlan], TabOutcome] = run_plan,
    fail_fast: bool = False,
) -> RunSummary:
    summary = RunSummary()
    for plan in plans:
        print(format_tab_header(plan), flush=True)
        tab_start = time.time()
        outcome = runner(plan)
        summary.outcomes.append(outcome)
        count, total = downloaded_since(plan.tab_dir, tab_start)
        files = "file" if count == 1 else "files"
        print(f"  downloaded {format_bytes(total)} ({count} {files})", flush=True)
        if outcome.returncode != 0 and fail_fast:
            break
    return summary
