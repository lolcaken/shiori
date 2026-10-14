"""Tests for shiori.runner.resolve — turning a channel URL into a display name."""
import pytest

from shiori.core.errors import ChannelResolveError, TabMissingError
from shiori.runner.resolve import (
    check_tab_exists,
    is_missing_tab,
    parse_channel_name,
    resolve_argv,
    resolve_channel_name,
    tab_probe_argv,
)


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


def test_tab_probe_argv_lists_without_downloading():
    argv = tab_probe_argv("yt-dlp", "https://www.youtube.com/@X/streams")
    assert "--flat-playlist" in argv
    assert "--skip-download" in argv
    assert argv[argv.index("--playlist-items") + 1] == "1"  # existence only, not the whole listing
    assert argv[-1] == "https://www.youtube.com/@X/streams"


def test_missing_tab_signature_is_detected():
    assert is_missing_tab(1, "ERROR: [youtube:tab] @X: This channel does not have a streams tab") is True
    assert is_missing_tab(0, "") is False
    assert is_missing_tab(1, "ERROR: [youtube] 123: Private video") is False


def test_check_tab_exists_raises_only_for_missing_tabs():
    def run_for(output, returncode):
        def fake_run(argv, **kwargs):
            class Completed:
                pass
            Completed.returncode = returncode
            Completed.stdout = output
            Completed.stderr = output
            return Completed()
        return fake_run

    with pytest.raises(TabMissingError):
        check_tab_exists(
            "yt-dlp", "https://www.youtube.com/@X/streams",
            run=run_for("This channel does not have a streams tab", 1),
        )
    # Any other outcome (even other errors) proceeds to download.
    check_tab_exists(
        "yt-dlp", "https://www.youtube.com/@X/videos",
        run=run_for("", 0),
    )
    check_tab_exists(
        "yt-dlp", "https://www.youtube.com/@X/videos",
        run=run_for("ERROR: network blip", 1),
    )
