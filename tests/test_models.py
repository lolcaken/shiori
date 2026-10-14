"""Tests for shiori.core.models — the shared vocabulary of the app."""
from pathlib import Path

import pytest

from shiori.core.models import DownloadPlan, Options, RunSummary, Tab, TabOutcome


def test_tab_covers_videos_shorts_and_streams():
    assert {t.value for t in Tab} == {"videos", "shorts", "streams"}


def test_options_stores_parsed_values():
    options = Options(
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
    assert options.tabs == (Tab.VIDEOS, Tab.SHORTS)
    assert options.jobs == 4


def test_empty_run_summary_counts_as_success():
    assert RunSummary().all_ok is True


def test_tab_outcome_counts_no_skips_by_default():
    assert TabOutcome(plan=None, returncode=0, elapsed=1.0).skipped == 0


def test_run_summary_reports_failure_when_any_tab_fails():
    def outcome(code):
        return TabOutcome(plan=None, returncode=code, elapsed=1.0)

    summary = RunSummary(outcomes=[outcome(0), outcome(1)])
    assert summary.all_ok is False
    assert len(summary.failed) == 1
    assert len(summary.succeeded) == 1


def test_download_plan_carries_its_argv():
    plan = DownloadPlan(
        tab=Tab.VIDEOS,
        url="https://www.youtube.com/@SomeChannel/videos",
        channel_name="Some Channel",
        channel_folder="Some Channel",
        tab_dir=Path("archives/Some Channel/videos"),
        archive_path=Path("archives/Some Channel/.shiori-archive.txt"),
        argv=["yt-dlp", "https://www.youtube.com/@SomeChannel/videos"],
    )
    assert plan.argv[0] == "yt-dlp"
    assert plan.tab is Tab.VIDEOS

    with pytest.raises(AttributeError):
        plan.tab = Tab.SHORTS  # frozen dataclass: plans are immutable
