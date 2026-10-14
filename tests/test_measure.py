"""Tests for shiori.runner.measure — bytes downloaded, measured from disk."""
import os
import time
from pathlib import Path

from shiori.runner.measure import downloaded_since, format_bytes


def test_format_bytes_uses_yt_dlp_style_units():
    assert format_bytes(0) == "0 B"
    assert format_bytes(512) == "512 B"
    assert format_bytes(2048) == "2.0 KiB"
    assert format_bytes(5 * 1024 * 1024) == "5.0 MiB"
    assert format_bytes(3 * 1024**3) == "3.0 GiB"


def test_downloaded_since_counts_only_files_written_after_the_mark(tmp_path):
    old = tmp_path / "old.mp4"
    old.write_bytes(b"x" * 1024)
    os.utime(old, (0, 0))  # long ago

    mark = time.time()
    new = tmp_path / "new.mp4"
    new.write_bytes(b"y" * 2048)

    count, total = downloaded_since(tmp_path, mark)
    assert (count, total) == (1, 2048)


def test_downloaded_since_on_a_missing_dir_is_zero():
    assert downloaded_since(Path("/no/such/dir-shiori"), time.time()) == (0, 0)
