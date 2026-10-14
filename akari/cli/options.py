"""Validate a parsed namespace into an immutable Options."""
from __future__ import annotations

import argparse
from pathlib import Path

from akari.core.errors import UsageError
from akari.core.models import Options, Tab

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
    return Options(
        url=ns.url,
        output_dir=Path(ns.output),
        tabs=tabs,
        sub_langs=ns.sub_langs,
        since=ns.since,
        until=ns.until,
        full=ns.full,
        jobs=ns.jobs,
        cookies=Path(ns.cookies) if ns.cookies else None,
        dry_run=ns.dry_run,
        yt_dlp=ns.yt_dlp,
        fail_fast=ns.fail_fast,
        channel_name=ns.channel_name,
        sleep_interval=ns.sleep,
    )
