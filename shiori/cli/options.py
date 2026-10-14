"""Validate a parsed namespace into an immutable Options."""
from __future__ import annotations

import argparse
from pathlib import Path

from shiori.core.errors import UsageError
from shiori.core.models import Options, Tab

_TYPE_TO_TABS: dict[str, tuple[Tab, ...]] = {
    "videos": (Tab.VIDEOS,),
    "shorts": (Tab.SHORTS,),
    "all": (Tab.VIDEOS, Tab.SHORTS, Tab.STREAMS),
}


def options_from_namespace(ns: argparse.Namespace) -> Options:
    if ns.jobs < 1:
        raise UsageError("--jobs must be at least 1")
    if ns.sleep < 0:
        raise UsageError("--sleep must not be negative")
    try:
        tabs = _TYPE_TO_TABS[ns.type]
    except KeyError:
        raise UsageError(f"unknown type {ns.type!r}") from None
    cookies = Path(ns.cookies) if ns.cookies else None
    if cookies is not None and not cookies.is_file():
        raise UsageError(f"--cookies file does not exist: {cookies}")
    return Options(
        url=ns.url,
        output_dir=Path(ns.output),
        tabs=tabs,
        sub_langs=ns.sub_langs,
        since=ns.since,
        until=ns.until,
        full=ns.full,
        jobs=ns.jobs,
        cookies=cookies,
        dry_run=ns.dry_run,
        yt_dlp=ns.yt_dlp,
        fail_fast=ns.fail_fast,
        channel_name=ns.channel_name,
        sleep_interval=ns.sleep,
        verbose=ns.verbose,
        throttled_rate=ns.throttled_rate,
        http_chunk_size=ns.http_chunk_size,
        force_ipv4=ns.ipv4,
        no_log=ns.no_log,
        no_color=ns.no_color,
    )
