"""Tests for akari.runner.process — running ONE plan as a subprocess."""
import sys
from pathlib import Path

from akari.core.models import DownloadPlan, Tab
from akari.runner.process import run_plan


def make_plan(argv):
    return DownloadPlan(
        tab=Tab.VIDEOS,
        url="https://www.youtube.com/@SomeChannel/videos",
        channel_name="Some Channel",
        channel_folder="Some Channel",
        tab_dir=Path("archives/Some Channel/videos"),
        archive_path=Path("archives/Some Channel/.akari-archive.txt"),
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
