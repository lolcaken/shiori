"""Tests for shiori.runner.process — running ONE plan as a subprocess."""
import io
import sys
from pathlib import Path

from shiori.core.models import DownloadPlan, Tab
from shiori.runner.process import run_plan


def make_plan(argv):
    return DownloadPlan(
        tab=Tab.VIDEOS,
        url="https://www.youtube.com/@SomeChannel/videos",
        channel_name="Some Channel",
        channel_folder="Some Channel",
        tab_dir=Path("archives/Some Channel/videos"),
        archive_path=Path("archives/Some Channel/.shiori-archive.txt"),
        argv=argv,
    )


def test_successful_command_reports_returncode_zero():
    outcome = run_plan(make_plan([sys.executable, "-c", "pass"]))
    assert outcome.returncode == 0
    assert outcome.plan.tab is Tab.VIDEOS
    assert outcome.elapsed >= 0


def test_failing_command_reports_its_returncode():
    outcome = run_plan(make_plan([sys.executable, "-c", "import sys; sys.exit(3)"]))
    assert outcome.returncode == 3


def test_progress_spam_collapses_into_one_done_line(capsys):
    script = "; ".join([
        "print('[download] Destination: some/video.mp4')",
        "print('[download]  10.0% of  10.00MiB at  5.00MiB/s ETA 00:01')",
        "print('[download]  63.9% of  10.00MiB at  Unknown B/s ETA Unknown')",
        "print('[download] 100% of  10.00MiB in 00:01 at  9.00MiB/s')",
    ])
    outcome = run_plan(make_plan([sys.executable, "-c", script]))
    out = capsys.readouterr().out
    assert outcome.returncode == 0
    assert "ok" in out and "video.mp4" in out
    assert "10.0% of" not in out  # raw progress spam never reaches the terminal
    assert "Downloading webpage" not in out


def test_error_lines_surface_live_and_are_counted(capsys):
    script = "print('ERROR: [youtube] 123: Private video')"
    outcome = run_plan(make_plan([sys.executable, "-c", script]))
    out = capsys.readouterr().out
    assert outcome.errors == 1
    assert "Private video" in out


def test_warnings_are_counted_not_shown_by_default(capsys):
    script = "print('WARNING: no subtitles for this one')"
    outcome = run_plan(make_plan([sys.executable, "-c", script]))
    out = capsys.readouterr().out
    assert outcome.warnings == 1
    assert "no subtitles" not in out


def test_merged_parts_collapse_into_one_ok_line_for_the_final_file(capsys):
    script = "; ".join([
        "print('[download] Destination: some/movie.f137.mp4')",
        "print('[download] 100% of  8.71MiB in 00:02')",
        "print('[download] Destination: some/movie.f140.m4a')",
        "print('[download] 100% of  448.87KiB in 00:00')",
        "print('[Merger] Merging formats into \"some/movie [en].mp4\"')",
    ])
    run_plan(make_plan([sys.executable, "-c", script]))
    out = capsys.readouterr().out
    assert out.count("  ok ") == 1
    assert "movie [en].mp4" in out
    assert "f137" not in out and "f140" not in out


def test_subtitle_sidecars_stay_silent(capsys):
    script = "; ".join([
        "print('[download] Destination: some/video.mp4')",
        "print('[download] 100% of  10.00MiB in 00:01')",
        "print('[download] Destination: some/video.en.vtt')",
        "print('[download] 100% of  28.73KiB in 00:00')",
    ])
    run_plan(make_plan([sys.executable, "-c", script]))
    out = capsys.readouterr().out
    assert out.count("  ok ") == 1
    assert "video.mp4 (10.00MiB" in out
    assert ".vtt" not in out


def test_verbose_passes_raw_lines_through(capsys):
    script = "print('[download]  10.0% of  10.00MiB at  5.00MiB/s ETA 00:01')"
    run_plan(make_plan([sys.executable, "-c", script]), verbose=True)
    assert "10.0% of" in capsys.readouterr().out


def test_live_status_updates_in_place_on_a_tty(monkeypatch):
    class TtyBuffer(io.StringIO):
        def isatty(self):
            return True

    buf = TtyBuffer()
    monkeypatch.setattr(sys, "stdout", buf)
    script = "; ".join([
        "print('[download] Destination: some/video.mp4')",
        "print('[download]  10.0% of  10.00MiB at  5.00MiB/s ETA 00:01')",
        "print('[download] 100% of  10.00MiB in 00:01')",
    ])
    run_plan(make_plan([sys.executable, "-c", script]), no_color=True)
    out = buf.getvalue()
    assert "\r  dl 10% of 10.00MiB" in out  # in-place status, no newline spam
    assert "\r  ok video.mp4" in out  # collapsed done line after clearing status


def test_tty_progress_lines_come_back_in_color(monkeypatch):
    class TtyBuffer(io.StringIO):
        def isatty(self):
            return True

    buf = TtyBuffer()
    monkeypatch.setattr(sys, "stdout", buf)
    monkeypatch.delenv("NO_COLOR", raising=False)
    script = "; ".join([
        "print('[download] Destination: some/video.mp4')",
        "print('[download]  10.0% of  10.00MiB at  5.00MiB/s ETA 00:01')",
        "print('[download] 100% of  10.00MiB in 00:01')",
    ])
    run_plan(make_plan([sys.executable, "-c", script]))
    out = buf.getvalue()
    assert "\x1b[36m10%\x1b[0m" in out  # the spam, highlighted
    assert "\r  dl " not in out  # no in-place collapsing when colored
    assert "  ok video.mp4" in out  # done line still printed


def test_no_color_flag_restores_plain_collapsing_on_a_tty(monkeypatch):
    class TtyBuffer(io.StringIO):
        def isatty(self):
            return True

    buf = TtyBuffer()
    monkeypatch.setattr(sys, "stdout", buf)
    monkeypatch.delenv("NO_COLOR", raising=False)
    script = "print('[download]  10.0% of  10.00MiB at  5.00MiB/s ETA 00:01')"
    run_plan(make_plan([sys.executable, "-c", script]), no_color=True)
    out = buf.getvalue()
    assert "\x1b[" not in out
    assert "\r  dl 10%" in out


def test_skips_are_counted_not_printed(capsys):
    script = "; ".join([
        "print('[download] aaa has already been recorded in the archive')",
        "print('[download] bbb has already been recorded in the archive')",
    ])
    outcome = run_plan(make_plan([sys.executable, "-c", script]))
    out = capsys.readouterr().out
    assert outcome.skipped == 2
    assert "already archived" not in out  # sequencer prints the collapsed total


def test_verbose_lists_each_skip(capsys):
    script = "print('[download] aaa has already been recorded in the archive')"
    outcome = run_plan(make_plan([sys.executable, "-c", script]), verbose=True)
    assert outcome.skipped == 1
    assert "has already been recorded in the archive" in capsys.readouterr().out


def test_remux_of_an_already_reported_file_prints_once(capsys):
    script = "; ".join([
        "print('[download] Destination: some/movie [en].mp4')",
        "print('[download] 100% of  10.00MiB in 00:01')",
        'print(\'[VideoRemuxer] Not remuxing media file "some/movie [en].mp4"; already is in target format mp4\')',
    ])
    run_plan(make_plan([sys.executable, "-c", script]))
    assert capsys.readouterr().out.count("  ok ") == 1


def test_remuxed_container_reports_the_final_mp4_name(capsys):
    script = "; ".join([
        "print('[download] Destination: some/movie [en].webm')",
        "print('[download] 100% of  10.00MiB in 00:01')",
        'print(\'[VideoRemuxer] Remuxing "some/movie [en].mp4"\')',
    ])
    run_plan(make_plan([sys.executable, "-c", script]))
    out = capsys.readouterr().out
    assert out.count("  ok ") == 1
    assert "movie [en].mp4" in out
    assert ".webm" not in out


def test_thumbnail_sidecars_stay_silent(capsys):
    script = "; ".join([
        "print('[download] Destination: some/thumb.webp')",
        "print('[download] 100% of  44.13KiB in 00:00')",
    ])
    run_plan(make_plan([sys.executable, "-c", script]))
    out = capsys.readouterr().out
    assert "  ok " not in out
    assert ".webp" not in out


def test_live_status_carries_the_archived_count_on_a_tty(monkeypatch):
    class TtyBuffer(io.StringIO):
        def isatty(self):
            return True

    buf = TtyBuffer()
    monkeypatch.setattr(sys, "stdout", buf)
    script = "; ".join([
        "print('[download] aaa has already been recorded in the archive')",
        "print('[download] Destination: some/video.mp4')",
        "print('[download]  10.0% of  10.00MiB at  5.00MiB/s ETA 00:01')",
    ])
    run_plan(make_plan([sys.executable, "-c", script]), no_color=True)
    out = buf.getvalue()
    assert "-- 1 archived" in out
    assert "(1 archived)" in out
