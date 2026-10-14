"""Tests for shiori.runner.highlight — ANSI colors for the download log."""
import sys

from shiori.runner.highlight import colorize_progress, enable_vt, use_color
from shiori.runner.progress import Progress


def test_percent_size_speed_eta_each_get_their_own_color():
    line = colorize_progress(
        Progress(54.7, "107.26MiB", "20.58MiB/s", "00:02"), trailing="video.mp4"
    )
    assert "\x1b[1m\x1b[36m54.7%\x1b[0m" in line  # bold cyan percent
    assert "\x1b[33m107.26MiB\x1b[0m" in line  # yellow size
    assert "\x1b[32m20.58MiB/s\x1b[0m" in line  # green speed
    assert "\x1b[35m00:02\x1b[0m" in line  # magenta ETA
    assert line.endswith("-- video.mp4")


def test_missing_speed_and_eta_are_omitted_not_colored():
    line = colorize_progress(Progress(63.9, "107.26MiB", None, None))
    assert " at " not in line
    assert "ETA" not in line


def test_use_color_needs_a_live_terminal(monkeypatch):
    monkeypatch.setattr(sys, "stdout", _NonTty())
    assert use_color(no_color=False) is False


def test_no_color_flag_disables_colors_even_on_a_tty(monkeypatch):
    monkeypatch.setattr(sys, "stdout", _Tty())
    assert use_color(no_color=True) is False


def test_no_color_env_var_disables_colors(monkeypatch):
    monkeypatch.setattr(sys, "stdout", _Tty())
    monkeypatch.setenv("NO_COLOR", "1")
    assert use_color(no_color=False) is False


def test_colors_enabled_on_a_live_terminal(monkeypatch):
    monkeypatch.setattr(sys, "stdout", _Tty())
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert use_color(no_color=False) is True


def test_enable_vt_never_raises():
    enable_vt()


class _Tty:
    def isatty(self):
        return True


class _NonTty:
    def isatty(self):
        return False
