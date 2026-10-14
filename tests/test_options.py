"""Tests for akari.cli.options — namespace validation into Options."""
import pytest

from akari.cli.options import options_from_namespace
from akari.cli.parser import build_parser
from akari.core.errors import UsageError
from akari.core.models import Tab


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
