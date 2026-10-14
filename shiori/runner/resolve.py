"""Resolve a channel URL to its display name with one lightweight yt-dlp call."""
from __future__ import annotations

import subprocess
from typing import Callable

from shiori.core.errors import ChannelResolveError


def resolve_argv(yt_dlp: str, channel_url: str) -> list[str]:
    return [
        yt_dlp,
        "--ignore-config",
        "--flat-playlist",
        "--playlist-items", "1",
        "--print", "%(playlist_uploader,playlist_uploader_id)s",
        "--skip-download",
        "--no-warnings",
        channel_url,
    ]


def parse_channel_name(output: str) -> str:
    for line in (output or "").splitlines():
        name = line.strip()
        if name:
            return name
    raise ChannelResolveError("yt-dlp returned no channel name for the URL")


def resolve_channel_name(
    yt_dlp: str,
    channel_url: str,
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> str:
    try:
        completed = run(
            resolve_argv(yt_dlp, channel_url),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ChannelResolveError(f"could not resolve the channel: {exc}") from exc
    if completed.returncode != 0:
        raise ChannelResolveError(
            "yt-dlp could not read the channel "
            "(private, deleted, or age/bot-gated — try --cookies)"
        )
    return parse_channel_name(completed.stdout)
