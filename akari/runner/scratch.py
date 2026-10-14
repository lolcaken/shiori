"""Lifecycle for the scratch dir that holds subtitle files mid-run.

Subtitles are written here (never next to the mp4) so the archive folder
ends up mp4-only; embedding reads them from here and the tree is removed
in a ``finally`` via TemporaryDirectory.
"""
from __future__ import annotations

import contextlib
import tempfile
from collections.abc import Iterator
from pathlib import Path


@contextlib.contextmanager
def scratch_dir(prefix: str = "akari-subs-") -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
        yield Path(tmp)
