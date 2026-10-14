"""Tests for shiori.runner.sequencer — plans run in order, outcomes aggregated."""
from pathlib import Path

from shiori.core.models import Options, Tab, TabOutcome
from shiori.planner.builder import build_plans
from shiori.runner.sequencer import run_all


def make_options(**overrides):
    base = dict(
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
    base.update(overrides)
    return Options(**base)


def stub_runner(returncodes):
    calls = []

    def run(plan):
        calls.append(plan)
        return TabOutcome(plan=plan, returncode=returncodes[len(calls) - 1], elapsed=0.5)

    run.calls = calls
    return run


def test_all_plans_run_in_order_and_summary_aggregates():
    plans = build_plans(make_options(), "Some Channel", Path("/tmp/subs"))
    runner = stub_runner([0, 0])
    summary = run_all(plans, runner=runner, fail_fast=False)
    assert [c.tab for c in runner.calls] == [Tab.VIDEOS, Tab.SHORTS]
    assert summary.all_ok is True


def test_without_fail_fast_a_failed_tab_does_not_stop_the_rest():
    plans = build_plans(make_options(), "Some Channel", Path("/tmp/subs"))
    runner = stub_runner([1, 0])
    summary = run_all(plans, runner=runner, fail_fast=False)
    assert len(runner.calls) == 2
    assert summary.all_ok is False


def test_fail_fast_stops_after_the_first_failure():
    plans = build_plans(make_options(), "Some Channel", Path("/tmp/subs"))
    runner = stub_runner([1, 0])
    run_all(plans, runner=runner, fail_fast=True)
    assert len(runner.calls) == 1


def test_each_tab_is_announced_as_it_starts(capsys):
    plans = build_plans(make_options(), "Some Channel", Path("/tmp/subs"))
    run_all(plans, runner=stub_runner([0, 0]), fail_fast=False)
    out = capsys.readouterr().out
    assert "videos" in out and "shorts" in out
