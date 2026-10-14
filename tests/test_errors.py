"""Tests for akari.core.errors — every failure maps to an exit code."""
from akari.core.errors import (
    AkariError,
    ChannelResolveError,
    PreflightError,
    UsageError,
)


def test_errors_form_a_hierarchy_under_akari_error():
    assert issubclass(UsageError, AkariError)
    assert issubclass(PreflightError, AkariError)
    assert issubclass(ChannelResolveError, AkariError)


def test_usage_errors_exit_with_code_2():
    assert UsageError("bad flag").exit_code == 2


def test_preflight_errors_exit_with_code_3():
    assert PreflightError("no ffmpeg").exit_code == 3


def test_channel_resolution_errors_exit_with_code_1():
    assert ChannelResolveError("private channel").exit_code == 1
