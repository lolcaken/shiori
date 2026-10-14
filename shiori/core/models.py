"""Shared vocabulary: the data shapes every layer passes around."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Tab(Enum):
    VIDEOS = "videos"
    SHORTS = "shorts"
    STREAMS = "streams"


@dataclass(frozen=True)
class Options:
    url: str
    output_dir: Path
    tabs: tuple[Tab, ...]
    sub_langs: str
    since: str | None
    until: str | None
    full: bool
    jobs: int
    cookies: Path | None
    dry_run: bool
    yt_dlp: str
    fail_fast: bool
    channel_name: str | None
    sleep_interval: float
    throttled_rate: str = "100K"
    http_chunk_size: str = "10M"
    force_ipv4: bool = False
    no_log: bool = False
    extractor_args: tuple[str, ...] = ()
    workers: int = 3
    min_disk_gb: float = 5.0
    no_lock: bool = False


@dataclass(frozen=True)
class DownloadPlan:
    tab: Tab
    url: str
    channel_name: str
    channel_folder: str
    tab_dir: Path
    archive_path: Path
    argv: list[str]


@dataclass(frozen=True)
class TabOutcome:
    plan: DownloadPlan | None
    returncode: int
    elapsed: float
    partial: bool = False
    skipped: bool = False


@dataclass
class RunSummary:
    outcomes: list[TabOutcome] = field(default_factory=list)

    @property
    def succeeded(self) -> list[TabOutcome]:
        return [o for o in self.outcomes if o.returncode == 0 and not o.skipped]

    @property
    def failed(self) -> list[TabOutcome]:
        return [o for o in self.outcomes if o.returncode != 0 and not o.partial]

    @property
    def partial(self) -> list[TabOutcome]:
        return [o for o in self.outcomes if o.partial]

    @property
    def skipped(self) -> list[TabOutcome]:
        return [o for o in self.outcomes if o.skipped]

    @property
    def all_ok(self) -> bool:
        return not self.failed
