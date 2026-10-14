"""Tests for shiori.runner.workers — parallel video downloads within a tab."""
import threading
import time
from pathlib import Path

from shiori.core.models import Options, Tab
from shiori.planner.builder import build_plans
from shiori.runner.workers import (
    chunk_ids,
    monitor_progress,
    run_plan_parallel,
    run_shard_commands,
)


def make_options(**overrides):
    base = dict(
        url="https://www.youtube.com/@SomeChannel",
        output_dir=Path("archives"),
        tabs=(Tab.VIDEOS,),
        sub_langs="en.*",
        since=None,
        until=None,
        full=False,
        jobs=8,
        cookies=None,
        dry_run=False,
        yt_dlp="yt-dlp",
        fail_fast=False,
        channel_name=None,
        sleep_interval=2.0,
    )
    base.update(overrides)
    return Options(**base)


def test_chunk_ids_splits_evenly_across_workers():
    assert chunk_ids(["a", "b", "c", "d", "e"], 2) == [["a", "b", "c"], ["d", "e"]]
    assert chunk_ids(["a"], 4) == [["a"]]
    assert chunk_ids([], 3) == []


def test_run_shard_commands_runs_everything_and_collects_codes_in_order():
    calls = []

    def fake_run(argv):
        calls.append(argv)
        return 0 if "good" in argv[-1] else 2

    codes = run_shard_commands(
        [["yt-dlp", "good"], ["yt-dlp", "bad"]], max_workers=2, run_fn=fake_run
    )
    assert codes == [0, 2]
    assert len(calls) == 2


def test_monitor_reports_completed_over_total_once(capsys, tmp_path):
    shard = tmp_path / "shard-0.txt"
    shard.write_text("youtube a\nyoutube b\n", encoding="utf-8")
    stop = threading.Event()
    thread = threading.Thread(
        target=monitor_progress,
        kwargs=dict(stop_event=stop, shard_files=[shard], total=5,
                    label="shorts", interval=0.01),
    )
    thread.start()
    time.sleep(0.05)
    stop.set()
    thread.join(timeout=5)
    out = capsys.readouterr().out
    assert "shorts: 2/5 videos" in out
    assert out.count("shorts: 2/5 videos") == 1


def test_parallel_full_loop_enumerates_filters_runs_and_merges(tmp_path):
    options = make_options(output_dir=tmp_path)
    plans = build_plans(options, "Some Channel", tmp_path / "subs")
    plan = plans[0]
    plan.archive_path.parent.mkdir(parents=True, exist_ok=True)
    plan.archive_path.write_text("youtube b\n", encoding="utf-8")

    def fake_list_ids(yt_dlp, tab_url):
        assert tab_url == plan.url
        return ["a", "b", "c"]

    def fake_run(argv):
        batch = Path(argv[argv.index("--batch-file") + 1])
        shard = Path(argv[argv.index("--download-archive") + 1])
        ids = [line.rsplit("v=", 1)[-1] for line in batch.read_text().splitlines()]
        with shard.open("a", encoding="utf-8") as handle:
            for video_id in ids:
                handle.write(f"youtube {video_id}\n")
        return 0

    outcome = run_plan_parallel(
        plan, yt_dlp="yt-dlp", workers=2, scratch_dir=tmp_path / "scratch",
        list_ids=fake_list_ids, run_fn=fake_run, monitor=False,
    )
    assert outcome.returncode == 0
    assert plan.archive_path.read_text().splitlines() == [
        "youtube b", "youtube a", "youtube c",
    ]


def test_parallel_skips_download_phase_when_everything_is_archived(tmp_path):
    options = make_options(output_dir=tmp_path)
    plans = build_plans(options, "Some Channel", tmp_path / "subs")
    plan = plans[0]
    plan.archive_path.parent.mkdir(parents=True, exist_ok=True)
    plan.archive_path.write_text("youtube a\n", encoding="utf-8")

    def boom(argv):
        raise AssertionError("no download should run")

    outcome = run_plan_parallel(
        plan, yt_dlp="yt-dlp", workers=2, scratch_dir=tmp_path / "scratch",
        list_ids=lambda *a: ["a"], run_fn=boom, monitor=False,
    )
    assert outcome.returncode == 0


def test_parallel_falls_back_to_classic_on_enumeration_failure(tmp_path, capsys):
    options = make_options(output_dir=tmp_path)
    plans = build_plans(options, "Some Channel", tmp_path / "subs")
    plan = plans[0]
    seen = []

    def failing_list_ids(yt_dlp, tab_url):
        raise OSError("no network")

    def fake_run(argv):
        seen.append(argv)
        return 0

    outcome = run_plan_parallel(
        plan, yt_dlp="yt-dlp", workers=2, scratch_dir=tmp_path / "scratch",
        list_ids=failing_list_ids, run_fn=fake_run, monitor=False,
    )
    assert outcome.returncode == 0
    assert seen == [plan.argv]  # the untouched single-shot tab command
