"""Tests for shiori.runner.preflight — required tools must exist before work starts."""
import sys
from pathlib import Path

import pytest

from shiori.core.errors import PreflightError
from shiori.runner.preflight import check_disk_space, find_binary, preflight, tool_version


def test_tool_version_runs_the_binary_and_returns_its_output():
    assert "Python" in tool_version(sys.executable, ["--version"])


def test_missing_binary_is_a_preflight_error():
    with pytest.raises(PreflightError):
        find_binary("shiori-definitely-not-a-real-binary")


def test_unrunnable_binary_is_a_preflight_error(tmp_path):
    fake = tmp_path / "not-executable-at-all"
    fake.write_text("this is not a program")
    with pytest.raises(PreflightError):
        tool_version(str(fake), ["--version"])


def test_preflight_confirms_yt_dlp_and_ffmpeg():
    tools = preflight("yt-dlp")
    assert "yt-dlp" in tools["yt-dlp"].lower() or tools["yt-dlp"][0].isdigit()
    assert "ffmpeg" in tools["ffmpeg"].lower()


def test_disk_space_check_passes_when_room_exists(tmp_path):
    check_disk_space(tmp_path, 0)
    check_disk_space(tmp_path / "not-created-yet", 0)


def test_disk_space_check_fails_cleanly_when_full():
    with pytest.raises(PreflightError):
        check_disk_space(Path("."), 10**12)
