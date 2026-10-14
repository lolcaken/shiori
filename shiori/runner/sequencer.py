"""Run plans sequentially and aggregate their outcomes.

Tabs run one at a time: parallel tabs against YouTube only invite
rate limiting, and a failure in one tab must not silently cancel the rest.
"""
from __future__ import annotations

from collections.abc import Callable

from shiori.core.models import DownloadPlan, RunSummary, TabOutcome
from shiori.runner.process import run_plan
from shiori.runner.reporting import format_archived_line, format_tab_header


def run_all(
    plans: list[DownloadPlan],
    runner: Callable[[DownloadPlan], TabOutcome] = run_plan,
    fail_fast: bool = False,
) -> RunSummary:
    summary = RunSummary()
    for plan in plans:
        print(format_tab_header(plan), flush=True)
        outcome = runner(plan)
        summary.outcomes.append(outcome)
        archived = format_archived_line(outcome.skipped)
        if archived:
            print(archived, flush=True)
        if outcome.returncode != 0 and fail_fast:
            break
    return summary
