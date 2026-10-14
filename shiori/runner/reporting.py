"""Render the end-of-run summary for the terminal."""
from __future__ import annotations

from shiori.core.models import DownloadPlan, RunSummary


def format_tab_header(plan: DownloadPlan) -> str:
    return f"== {plan.tab.value} ==  {plan.url}"


def format_archived_line(skipped: int) -> str:
    """One collapsed line for a tab's already-archived videos ("" when none)."""
    return f"  {skipped} already archived" if skipped else ""


def format_summary(summary: RunSummary) -> str:
    lines = []
    for outcome in summary.outcomes:
        if outcome.returncode == 0:
            continue  # success already has its ok lines; only failures repeat
        tab = outcome.plan.tab.value if outcome.plan is not None else "?"
        lines.append(
            f"  FAIL  {tab:<8} rc={outcome.returncode} ({outcome.elapsed:.1f}s)"
        )
    tabs = "tab" if len(summary.outcomes) == 1 else "tabs"
    lines.append(
        f"Archive run: {len(summary.outcomes)} {tabs}, "
        f"{len(summary.succeeded)} ok, {len(summary.failed)} failed"
    )
    warnings = sum(o.warnings for o in summary.outcomes)
    if warnings:
        lines.append(
            f"  {warnings} warnings suppressed (re-run with --verbose to see them)"
        )
    return "\n".join(lines)
