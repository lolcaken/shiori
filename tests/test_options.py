"""Tests for shiori.cli.options — namespace validation into Options."""
import pytest

from shiori.cli.options import options_from_namespace
from shiori.cli.parser import build_parser
from shiori.core.errors import UsageError
from shiori.core.models import Tab


def parse(args):
    return options_from_namespace(build_parser().parse_args(args))


def test_type_videos_selects_only_the_videos_tab():
    assert parse(["https://x"]) .tabs == (Tab.VIDEOS,)


def test_type_all_selects_videos_shorts_and_streams():
    assert parse(["https://x", "--type", "all"]).tabs == (
        Tab.VIDEOS, Tab.SHORTS, Tab.STREAMS,
    )


def test_zero_jobs_is_rejected():
    with pytest.raises(UsageError):
        parse(["https://x", "-j", "0"])


def test_output_becomes_a_path_and_cookies_survive(tmp_path):
    cookies = tmp_path / "c.txt"
    cookies.write_text("# Netscape HTTP Cookie File\n")
    options = parse(["https://x", "-o", "out", "--cookies", str(cookies)])
    assert str(options.output_dir) == "out"
    assert options.cookies == cookies


def test_missing_cookies_file_is_rejected_before_any_download():
    with pytest.raises(UsageError):
        parse(["https://x", "--cookies", "no-such-cookies.txt"])


def test_throttle_options_default_and_override():
    defaults = parse(["https://x"])
    assert defaults.throttled_rate == "100K"
    assert defaults.http_chunk_size == "10M"
    assert defaults.force_ipv4 is False
    tuned = parse([
        "https://x", "--throttled-rate", "0",
        "--http-chunk-size", "5M", "--ipv4",
    ])
    assert tuned.throttled_rate == "0"
    assert tuned.http_chunk_size == "5M"
    assert tuned.force_ipv4 is True


def test_log_file_is_opt_out():
    assert parse(["https://x"]).no_log is False
    assert parse(["https://x", "--no-log"]).no_log is True


def test_workers_default_to_three_and_reject_zero():
    assert parse(["https://x"]).workers == 3
    assert parse(["https://x", "--workers", "1"]).workers == 1
    with pytest.raises(UsageError):
        parse(["https://x", "--workers", "0"])


def test_disk_threshold_default_and_negative_rejected():
    assert parse(["https://x"]).min_disk_gb == 5.0
    with pytest.raises(UsageError):
        parse(["https://x", "--min-disk-gb", "-1"])


def test_lock_is_opt_out():
    assert parse(["https://x"]).no_lock is False
    assert parse(["https://x", "--no-lock"]).no_lock is True


def test_extractor_args_default_empty_and_repeatable():
    assert parse(["https://x"]).extractor_args == ()
    options = parse([
        "https://x",
        "--extractor-args", "youtube:player_client=web_embedded",
        "--extractor-args", "youtube:player_skip=webpage",
    ])
    assert options.extractor_args == (
        "youtube:player_client=web_embedded",
        "youtube:player_skip=webpage",
    )


def test_extractor_args_must_be_key_colon_args():
    with pytest.raises(UsageError):
        parse(["https://x", "--extractor-args", "player_client"])
