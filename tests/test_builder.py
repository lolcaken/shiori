"""Tests for shiori.planner.builder — Options + channel name -> DownloadPlans."""
from pathlib import Path

from shiori.core.models import Options, Tab
from shiori.planner.builder import build_plans


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


def test_one_plan_per_requested_tab_with_matching_urls():
    plans = build_plans(make_options(), "Some Channel", Path("/tmp/subs"))
    assert [p.tab for p in plans] == [Tab.VIDEOS, Tab.SHORTS]
    assert plans[0].url.endswith("/videos")
    assert plans[1].url.endswith("/shorts")


def test_plans_share_one_channel_folder_and_archive_file():
    plans = build_plans(make_options(), "Some Channel", Path("/tmp/subs"))
    assert plans[0].channel_folder == "Some Channel"
    assert plans[0].archive_path == plans[1].archive_path
    assert plans[0].archive_path.name == ".shiori-archive.txt"


def test_tab_dirs_are_split_per_category():
    plans = build_plans(make_options(), "Some Channel", Path("/tmp/subs"))
    assert plans[0].tab_dir == Path("archives/Some Channel/videos")
    assert plans[1].tab_dir == Path("archives/Some Channel/shorts")


def test_argv_embeds_subs_into_mp4_and_points_output_at_the_tab_dir():
    plans = build_plans(make_options(), "Some Channel", Path("/tmp/subs"))
    argv = " ".join(plans[0].argv)
    assert "-t mp4" in argv
    assert "--embed-subs" in argv
    assert "--sub-langs en.*" in argv
    assert "--ignore-config" in argv
    assert "--throttled-rate 100K" in argv
    assert "--http-chunk-size 10M" in argv
    assert "--force-ipv4" not in argv
    assert plans[0].url in plans[0].argv  # the tab URL is the positional
    video_templates = [
        plans[0].argv[i + 1] for i, a in enumerate(plans[0].argv[:-1])
        if a == "-o" and not plans[0].argv[i + 1].startswith("subtitle:")
    ]
    assert len(video_templates) == 1
    assert "[en]" in video_templates[0]
    assert "archives/Some Channel/videos" in video_templates[0].replace("\\", "/")


def test_subtitles_are_routed_to_an_exact_scratch_template():
    plans = build_plans(make_options(), "Some Channel", Path("/tmp/subs"))
    argv = plans[0].argv
    subtitle_templates = [
        argv[i + 1] for i, a in enumerate(argv[:-1])
        if a == "-o" and argv[i + 1].startswith("subtitle:")
    ]
    assert len(subtitle_templates) == 1
    assert "/tmp/subs" in subtitle_templates[0].replace("\\", "/")
    assert "--paths" not in argv  # --paths prepends; exact template replaces


def test_date_range_and_cookies_propagate_into_argv():
    plans = build_plans(
        make_options(since="20240101", until="20241231", cookies=Path("c.txt")),
        "Some Channel",
        Path("/tmp/subs"),
    )
    argv = plans[0].argv
    assert "--dateafter 20240101" in " ".join(argv)
    assert "--datebefore 20241231" in " ".join(argv)
    assert argv[argv.index("--cookies") + 1] == "c.txt"


def test_full_rebuild_drops_the_archive_flag():
    plans = build_plans(make_options(full=True), "Some Channel", Path("/tmp/subs"))
    assert "--download-archive" not in plans[0].argv


def test_extractor_args_land_in_argv_before_the_url():
    plans = build_plans(
        make_options(extractor_args=("youtube:player_client=web_embedded",)),
        "Some Channel",
        Path("/tmp/subs"),
    )
    argv = plans[0].argv
    assert argv[argv.index("--extractor-args") + 1] == "youtube:player_client=web_embedded"
    assert argv.index("--extractor-args") < argv.index(plans[0].url)


def test_channel_name_is_sanitized_for_the_folder():
    plans = build_plans(make_options(), "Some: Channel?", Path("/tmp/subs"))
    assert plans[0].channel_folder == "Some_ Channel_"


def test_worker_argv_swaps_url_for_batch_file_and_shards_archive():
    from shiori.planner.builder import worker_argv

    plans = build_plans(make_options(), "Some Channel", Path("/tmp/subs"))
    argv = plans[0].argv
    worker = worker_argv(argv, Path("/tmp/b0.txt"), Path("/tmp/a0.txt"))
    assert worker[-2:] == ["--batch-file", str(Path("/tmp/b0.txt"))]
    assert worker[worker.index("--download-archive") + 1] == str(Path("/tmp/a0.txt"))
    assert plans[0].url not in worker
    assert len(worker) == len(argv) + 1  # positional became two flag parts
