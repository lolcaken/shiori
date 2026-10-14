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


def test_parallel_runner_replaces_the_default_runner():
    plans = build_plans(make_options(), "Some Channel", Path("/tmp/subs"))
    calls = []

    def parallel(plan):
        calls.append(plan)
        return TabOutcome(plan=plan, returncode=0, elapsed=1.0)

    def boom(plan):
        raise AssertionError("default runner must not run")

    summary = run_all([plans[0]], runner=boom, fail_fast=False, parallel=parallel)
    assert [c.tab for c in calls] == [Tab.VIDEOS]
    assert summary.all_ok is True


def test_missing_tab_is_skipped_not_failed(capsys):
    from shiori.core.errors import TabMissingError

    plans = build_plans(make_options(), "Some Channel", Path("/tmp/subs"))

    def probe(plan):
        if plan.tab is Tab.SHORTS:
            raise TabMissingError("no shorts tab")

    summary = run_all(plans, runner=stub_runner([0]), fail_fast=False, probe=probe)
    out = capsys.readouterr().out
    assert "-- no shorts tab, skipping" in out
    assert summary.all_ok is True
    assert len(summary.skipped) == 1
    assert len(summary.succeeded) == 1


def test_errored_tab_with_new_files_is_partial_not_failed(capsys, tmp_path):
    options = make_options(output_dir=tmp_path)
    plans = build_plans(options, "Some Channel", tmp_path / "subs")

    def runner(plan):
        plan.tab_dir.mkdir(parents=True, exist_ok=True)
        (plan.tab_dir / "new.mp4").write_bytes(b"y" * 1024)
        return TabOutcome(plan=plan, returncode=1, elapsed=0.5)

    summary = run_all([plans[0]], runner=runner, fail_fast=False)
    out = capsys.readouterr().out
    assert "completed with errors" in out
    assert summary.all_ok is True
    assert len(summary.partial) == 1


def test_errored_tab_with_no_new_files_is_a_real_failure(capsys, tmp_path):
    options = make_options(output_dir=tmp_path)
    plans = build_plans(options, "Some Channel", tmp_path / "subs")

    def runner(plan):
        return TabOutcome(plan=plan, returncode=1, elapsed=0.5)

    summary = run_all([plans[0]], runner=runner, fail_fast=False)
    assert "completed with errors" not in capsys.readouterr().out
    assert summary.all_ok is False


def test_each_tab_reports_bytes_downloaded(capsys, tmp_path):
    options = make_options(output_dir=tmp_path)
    plans = build_plans(options, "Some Channel", tmp_path / "subs")

    def runner(plan):
        plan.tab_dir.mkdir(parents=True, exist_ok=True)
        (plan.tab_dir / "new.mp4").write_bytes(b"y" * 2048)
        return TabOutcome(plan=plan, returncode=0, elapsed=0.5)

    run_all([plans[0]], runner=runner, fail_fast=False)
    out = capsys.readouterr().out
    assert "downloaded 2.0 KiB (1 file)" in out
