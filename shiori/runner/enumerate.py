"""List a tab's video IDs without downloading anything.

Used by parallel mode to split the work up front — which also yields
exact totals ("143/500") and lets fully-archived tabs skip the download
phase entirely.
"""
from __future__ import annotations

import subprocess
from typing import Callable


def list_tab_ids(
    yt_dlp: str,
    tab_url: str,
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> list[str]:
    completed = run(
        [
            yt_dlp,
            "--ignore-config",
            "--flat-playlist",
            "--print", "%(id)s",
            "--skip-download",
            "--no-warnings",
            tab_url,
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if completed.returncode != 0:
        raise OSError(f"could not list {tab_url}")
    return [
        line.strip()
        for line in (completed.stdout or "").splitlines()
        if line.strip() and line.strip() != "NA"
    ]
