"""Tests for shiori.channel.tabs — the registry mapping tabs to URL/folder."""
import pytest

from shiori.channel.tabs import spec_for
from shiori.core.models import Tab


def test_every_tab_has_a_spec():
    for tab in Tab:
        spec = spec_for(tab)
        assert spec.tab is tab


def test_videos_tab_points_at_videos_suffix_and_folder():
    spec = spec_for(Tab.VIDEOS)
    assert spec.url_suffix == "videos"
    assert spec.folder == "videos"


def test_shorts_tab_points_at_shorts_suffix_and_folder():
    spec = spec_for(Tab.SHORTS)
    assert spec.url_suffix == "shorts"
    assert spec.folder == "shorts"


def test_streams_tab_points_at_streams_suffix_and_folder():
    spec = spec_for(Tab.STREAMS)
    assert spec.url_suffix == "streams"
    assert spec.folder == "streams"


def test_unknown_tab_raises():
    with pytest.raises(KeyError):
        spec_for("playlists")
