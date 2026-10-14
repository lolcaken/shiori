"""Registry mapping each channel tab to its URL suffix and output folder."""
from __future__ import annotations

from dataclasses import dataclass

from shiori.core.models import Tab


@dataclass(frozen=True)
class TabSpec:
    tab: Tab
    url_suffix: str
    folder: str


TAB_SPECS: dict[Tab, TabSpec] = {
    Tab.VIDEOS: TabSpec(Tab.VIDEOS, "videos", "videos"),
    Tab.SHORTS: TabSpec(Tab.SHORTS, "shorts", "shorts"),
    Tab.STREAMS: TabSpec(Tab.STREAMS, "streams", "streams"),
}


def spec_for(tab: Tab) -> TabSpec:
    return TAB_SPECS[tab]
