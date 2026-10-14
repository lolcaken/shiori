"""Tests for akari.cli.parser — the argument surface."""
import pytest

from akari.cli.parser import build_parser


def test_defaults_archive_videos_with_english_subs():
    ns = build_parser().parse_args(["https://www.youtube.com/@SomeChannel"])
    assert ns.url == "https://www.youtube.com/@SomeChannel"
    assert ns.type == "videos"
    assert ns.sub_langs == "en.*"
    assert ns.output == "archives"
    assert ns.jobs == 8
    assert ns.throttled_rate == "100K"
    assert ns.http_chunk_size == "10M"
    assert ns.ipv4 is False
    assert ns.sleep == 2.0
    assert ns.dry_run is False
    assert ns.fail_fast is False
    assert ns.full is False
    assert ns.channel_name is None


def test_full_option_set_parses():
    ns = build_parser().parse_args([
        "https://www.youtube.com/@SomeChannel",
        "--type", "all",
        "-o", "out",
        "--sub-langs", "en.*,ja",
        "--since", "20240101",
        "--until", "20241231",
        "--full",
        "-j", "8",
        "--cookies", "cookies.txt",
        "--throttled-rate", "50K",
        "--http-chunk-size", "5M",
        "--ipv4",
        "--dry-run",
        "--yt-dlp", "yt-dlp.exe",
        "--fail-fast",
        "--channel-name", "Some Channel",
        "--sleep", "5",
    ])
    assert ns.type == "all"
    assert ns.output == "out"
    assert ns.jobs == 8
    assert ns.throttled_rate == "50K"
    assert ns.http_chunk_size == "5M"
    assert ns.ipv4 is True
    assert ns.cookies == "cookies.txt"
    assert ns.channel_name == "Some Channel"


def test_unknown_type_is_rejected_with_exit_code_2():
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["https://x", "--type", "playlists"])
    assert exc.value.code == 2
