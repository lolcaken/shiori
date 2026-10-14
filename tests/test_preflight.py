"""Tests for akari.runner.preflight — required tools must exist before work starts."""
import sys

import pytest

from akari.core.errors import PreflightError
from akari.runner.preflight import find_binary, preflight, tool_version


def test_tool_version_runs_the_binary_and_returns_its_output():
    assert "Python" in tool_version(sys.executable, ["--version"])


def test_missing_binary_is_a_preflight_error():
    with pytest.raises(PreflightError):
        find_binary("akari-definitely-not-a-real-binary")


def test_unrunnable_binary_is_a_preflight_error(tmp_path):
    fake = tmp_path / "not-executable-at-all"
    fake.write_text("this is not a program")
    with pytest.raises(PreflightError):
        tool_version(str(fake), ["--version"])


def test_preflight_confirms_yt_dlp_and_ffmpeg():
    tools = preflight("yt-dlp")
    assert "yt-dlp" in tools["yt-dlp"].lower() or tools["yt-dlp"][0].isdigit()
    assert "ffmpeg" in tools["ffmpeg"].lower()
