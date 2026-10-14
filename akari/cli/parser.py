"""The command-line surface: one parser, built in exactly one place."""
from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="akari",
        description=(
            "Archive a YouTube channel to local mp4 files with embedded "
            "soft subtitles. Re-runs only fetch new uploads."
        ),
    )
    parser.add_argument("url", help="channel URL (@handle, /channel/…, /c/…, /user/…)")
    parser.add_argument(
        "-o", "--output", default="archives",
        help="archive root directory (default: ./archives)",
    )
    parser.add_argument(
        "-t", "--type", default="videos", choices=("videos", "shorts", "all"),
        help="which channel tabs to archive (default: videos)",
    )
    parser.add_argument(
        "--sub-langs", default="en.*",
        help='subtitle languages, yt-dlp syntax (default: "en.*", use "all" for everything)',
    )
    parser.add_argument("--since", default=None, help="only videos on/after DATE (YYYYMMDD)")
    parser.add_argument("--until", default=None, help="only videos on/before DATE (YYYYMMDD)")
    parser.add_argument(
        "--full", action="store_true",
        help="ignore the archive file and re-download everything",
    )
    parser.add_argument(
        "-j", "--jobs", type=int, default=8,
        help="concurrent download fragments per video (default: 8)",
    )
    parser.add_argument(
        "--cookies", default=None,
        help="Netscape cookie jar for age/bot-gated channels",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="print the yt-dlp commands without running anything",
    )
    parser.add_argument(
        "--yt-dlp", default="yt-dlp", help="yt-dlp binary to use (default: from PATH)"
    )
    parser.add_argument(
        "--fail-fast", action="store_true",
        help="stop remaining tabs after the first failure",
    )
    parser.add_argument(
        "--channel-name", default=None,
        help="skip channel-name lookup (also keeps --dry-run offline)",
    )
    parser.add_argument(
        "--sleep", type=float, default=2.0,
        help="seconds between requests (default: 2.0)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="show raw yt-dlp output instead of organized logging",
    )
    parser.add_argument(
        "--throttled-rate", default="100K",
        help="re-extract when download rate drops below this (default: 100K, 0 disables)",
    )
    parser.add_argument(
        "--http-chunk-size", default="10M",
        help="size of chunked HTTP range requests (default: 10M)",
    )
    parser.add_argument(
        "--ipv4", action="store_true",
        help="force all connections over IPv4",
    )
    return parser
