"""Tests for akari.runner.resolve — turning a channel URL into a display name."""
import pytest

from akari.core.errors import ChannelResolveError
from akari.runner.resolve import parse_channel_name, resolve_argv, resolve_channel_name


def test_resolve_argv_is_a_lightweight_flat_playlist_print():
    argv = resolve_argv("yt-dlp", "https://www.youtube.com/@SomeChannel")
    assert "--flat-playlist" in argv
    assert "--skip-download" in argv
    printed = argv[argv.index("--print") + 1]
    assert "playlist_uploader" in printed  # display name, not the per-video uploader
    assert argv[-1] == "https://www.youtube.com/@SomeChannel"


def test_parse_takes_the_first_non_empty_line():
    assert parse_channel_name("Some Channel\nOther\n") == "Some Channel"


def test_parse_rejects_empty_output():
    with pytest.raises(ChannelResolveError):
        parse_channel_name("  \n ")


def test_resolve_runs_argv_and_parses_output():
    seen = {}

    def fake_run(argv, **kwargs):
        seen["argv"] = argv

        class Completed:
            returncode = 0
            stdout = "Some Channel\n"

        return Completed()

    name = resolve_channel_name(
        "yt-dlp", "https://www.youtube.com/@SomeChannel", run=fake_run
    )
    assert name == "Some Channel"
    assert seen["argv"][-1] == "https://www.youtube.com/@SomeChannel"


def test_resolve_failure_is_a_channel_error():
    def failing_run(argv, **kwargs):
        raise OSError("no network")

    with pytest.raises(ChannelResolveError):
        resolve_channel_name("yt-dlp", "https://www.youtube.com/@X", run=failing_run)
