"""Tests for akari.channel.urls — normalizing channel URLs, building tab URLs."""
import pytest

from akari.channel.urls import normalize_channel_url, tab_url
from akari.core.errors import UsageError
from akari.core.models import Tab


def test_trailing_slash_is_stripped():
    assert (
        normalize_channel_url("https://www.youtube.com/@SomeChannel/")
        == "https://www.youtube.com/@SomeChannel"
    )


def test_trailing_tab_suffix_is_stripped_so_reappending_is_idempotent():
    assert (
        normalize_channel_url("https://www.youtube.com/@SomeChannel/videos")
        == "https://www.youtube.com/@SomeChannel"
    )
    assert (
        normalize_channel_url("https://www.youtube.com/@SomeChannel/shorts")
        == "https://www.youtube.com/@SomeChannel"
    )


def test_bare_handle_expands_to_full_url():
    assert (
        normalize_channel_url("@SomeChannel")
        == "https://www.youtube.com/@SomeChannel"
    )


def test_channel_id_url_passes_through():
    url = "https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxxxx"
    assert normalize_channel_url(url) == url


def test_empty_url_is_rejected():
    with pytest.raises(UsageError):
        normalize_channel_url("   ")


def test_watch_url_is_rejected_because_it_is_not_a_channel():
    with pytest.raises(UsageError):
        normalize_channel_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


def test_tab_url_appends_the_tab_suffix():
    base = "https://www.youtube.com/@SomeChannel"
    assert tab_url(base, Tab.VIDEOS) == f"{base}/videos"
    assert tab_url(base, Tab.SHORTS) == f"{base}/shorts"
    assert tab_url(base, Tab.STREAMS) == f"{base}/streams"
