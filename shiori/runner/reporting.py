"""Render the end-of-run summary for the terminal."""
from __future__ import annotations

from shiori.core.models import DownloadPlan, RunSummary


def format_tab_header(plan: DownloadPlan) -> str:
    return f"== {plan.tab.value} ==  {plan.url}"


def format_tab_skipped(plan: DownloadPlan) -> str:
    return f"  -- no {plan.tab.value} tab, skipping"


def format_summary(summary: RunSummary) -> str:
    lines = []
    for outcome in summary.outcomes:
        if outcome.returncode == 0 or outcome.partial:
            continue  # successes (and partials) already have their own lines
        tab = outcome.plan.tab.value if outcome.plan is not None else "?"
        lines.append(
            f"  FAIL  {tab:<8} rc={outcome.returncode} ({outcome.elapsed:.1f}s)"
        )
    tabs = "tab" if len(summary.outcomes) == 1 else "tabs"
    parts = [
        f"{len(summary.outcomes)} {tabs}",
        f"{len(summary.succeeded)} ok",
    ]
    if summary.partial:
        parts.append(f"{len(summary.partial)} with errors")
    if summary.skipped:
        parts.append(f"{len(summary.skipped)} skipped")
    parts.append(f"{len(summary.failed)} failed")
    lines.append("Archive run: " + ", ".join(parts))
    return "\n".join(lines)
