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


def test_skipped_files_get_one_line(capsys):
    script = "print('[download] some/video.mp4 has already been downloaded')"
    run_plan(make_plan([sys.executable, "-c", script]))
    out = capsys.readouterr().out
    assert "skip" in out and "video.mp4" in out


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
    run_plan(make_plan([sys.executable, "-c", script]))
    out = buf.getvalue()
    assert "\r  dl 10% of 10.00MiB" in out  # in-place status, no newline spam
    assert "\r  ok video.mp4" in out  # collapsed done line after clearing status
