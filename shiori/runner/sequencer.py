"""Run plans sequentially and aggregate their outcomes.

Tabs run one at a time: parallel tabs against YouTube only invite
rate limiting, and a failure in one tab must not silently cancel the rest.
"""
from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import replace

from shiori.core.errors import TabMissingError
from shiori.core.models import DownloadPlan, RunSummary, TabOutcome
from shiori.runner.measure import downloaded_since, format_bytes
from shiori.runner.process import run_plan
from shiori.runner.reporting import format_tab_header, format_tab_skipped


def run_all(
    plans: list[DownloadPlan],
    runner: Callable[[DownloadPlan], TabOutcome] = run_plan,
    fail_fast: bool = False,
    probe: Callable[[DownloadPlan], None] | None = None,
) -> RunSummary:
    summary = RunSummary()
    for plan in plans:
        print(format_tab_header(plan), flush=True)
        if probe is not None:
            try:
                probe(plan)
            except TabMissingError:
                print(format_tab_skipped(plan), flush=True)
                summary.outcomes.append(
                    TabOutcome(plan=plan, returncode=0, elapsed=0.0, skipped=True)
                )
                continue
        tab_start = time.time()
        outcome = runner(plan)
        count, total = downloaded_since(plan.tab_dir, tab_start)
        files = "file" if count == 1 else "files"
        print(f"  downloaded {format_bytes(total)} ({count} {files})", flush=True)
        if outcome.returncode != 0 and count > 0:
            outcome = replace(outcome, partial=True)
            print("  completed with errors (see log)", flush=True)
        summary.outcomes.append(outcome)
        if outcome.returncode != 0 and fail_fast and not outcome.partial:
            break
    return summary
