"""Tests for shiori.runner.reporting — the human-readable end-of-run summary."""
from dataclasses import replace
from pathlib import Path

from shiori.core.models import Options, RunSummary, Tab, TabOutcome
from shiori.planner.builder import build_plans
from shiori.runner.reporting import (
    format_summary,
    format_tab_header,
    format_tab_skipped,
)


def make_options():
    return Options(
        url="https://www.youtube.com/@SomeChannel",
        output_dir=Path("archives"),
        tabs=(Tab.VIDEOS, Tab.SHORTS),
        sub_langs="en.*",
        since=None,
        until=None,
        full=False,
        jobs=4,
        cookies=None,
        dry_run=False,
        yt_dlp="yt-dlp",
        fail_fast=False,
        channel_name=None,
        sleep_interval=2.0,
    )


def test_summary_names_each_tab_and_totals():
    plans = build_plans(make_options(), "Some Channel", Path("/tmp/subs"))
    summary = RunSummary(
        outcomes=[
            TabOutcome(plan=plans[0], returncode=0, elapsed=12.3),
            TabOutcome(plan=plans[1], returncode=1, elapsed=4.1),
        ]
    )
    text = format_summary(summary)
    assert "FAIL" in text
    assert "shorts" in text
    assert "\n  ok " not in text  # successes already have their own ok lines
    assert "1 ok" in text
    assert "1 failed" in text


def test_summary_uses_singular_tab_for_one_plan():
    plans = build_plans(make_options(), "Some Channel", Path("/tmp/subs"))
    summary = RunSummary(outcomes=[TabOutcome(plan=plans[0], returncode=0, elapsed=1.0)])
    assert "1 tab," in format_summary(summary)


def test_tab_header_names_the_tab_and_url():
    plans = build_plans(make_options(), "Some Channel", Path("/tmp/subs"))
    header = format_tab_header(plans[0])
    assert "videos" in header
    assert plans[0].url in header


def test_tab_skipped_line_names_the_missing_tab():
    options = replace(
        make_options(), tabs=(Tab.VIDEOS, Tab.SHORTS, Tab.STREAMS)
    )
    plans = build_plans(options, "Some Channel", Path("/tmp/subs"))
    assert format_tab_skipped(plans[2]) == "  -- no streams tab, skipping"


def test_summary_composes_partial_and_skipped_counts():
    options = replace(
        make_options(), tabs=(Tab.VIDEOS, Tab.SHORTS, Tab.STREAMS)
    )
    plans = build_plans(options, "Some Channel", Path("/tmp/subs"))
    summary = RunSummary(outcomes=[
        TabOutcome(plan=plans[0], returncode=0, elapsed=1.0),
        TabOutcome(plan=plans[1], returncode=1, elapsed=1.0, partial=True),
        TabOutcome(plan=plans[2], returncode=0, elapsed=0.0, skipped=True),
    ])
    text = format_summary(summary)
    assert "1 ok" in text
    assert "1 with errors" in text
    assert "1 skipped" in text
    assert "0 failed" in text
