"""Render the end-of-run summary for the terminal."""
from __future__ import annotations

from akari.core.models import RunSummary


def format_summary(summary: RunSummary) -> str:
    lines = []
    for outcome in summary.outcomes:
        tab = outcome.plan.tab.value if outcome.plan is not None else "?"
        if outcome.returncode == 0:
            lines.append(f"  ok    {tab:<8} ({outcome.elapsed:.1f}s)")
        else:
            lines.append(
                f"  FAIL  {tab:<8} rc={outcome.returncode} ({outcome.elapsed:.1f}s)"
            )
    lines.append(
        f"Archive run: {len(summary.outcomes)} tabs, "
        f"{len(summary.succeeded)} ok, {len(summary.failed)} failed"
    )
    return "\n".join(lines)
