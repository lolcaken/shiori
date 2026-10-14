"""Read and merge yt-dlp download archives.

Archive lines look like ``youtube <video-id>``. Parallel workers each
write their own shard file (concurrent appends to one file would
interleave); the shards are unioned back into the main archive at the
end of the tab. Foreign lines are preserved untouched.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def read_archive_ids(path: Path) -> set[str]:
    """Return the set of archived video IDs (last token of each line)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return set()
    return {line.split()[-1] for line in text.splitlines() if line.split()}


def merge_archives(shards: list[Path], main: Path, dest: Path) -> None:
    """Union main archive + shards into dest, first-seen order, no dupes.

    Written atomically (temp file + replace) so an interrupted merge
    can never leave a half-written archive behind.
    """
    seen: set[str] = set()
    merged: list[str] = []
    for path in [main, *shards]:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if line and line not in seen:
                seen.add(line)
                merged.append(line)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(dest.parent), prefix=".shiori-archive-", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write("\n".join(merged))
            if merged:
                handle.write("\n")
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    os.replace(tmp_name, dest)
