"""Run plans sequentially and aggregate their outcomes.

Tabs run one at a time: parallel tabs against YouTube only invite
rate limiting, and a failure in one tab must not silently cancel the rest.
"""
from __future__ import annotations

from collections.abc import Callable

from akari.core.models import DownloadPlan, RunSummary, TabOutcome
from akari.runner.process import run_plan
from akari.runner.reporting import format_tab_header


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
        if outcome.returncode != 0 and fail_fast:
            break
    return summary
