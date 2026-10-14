"""Tests for shiori.runner.archive — reading and merging download archives."""
from shiori.runner.archive import merge_archives, read_archive_ids


def test_read_archive_ids_parses_extractor_id_lines(tmp_path):
    archive = tmp_path / "main.txt"
    archive.write_text("youtube abc123\n\nyoutube def456\nvimeo 999\n", encoding="utf-8")
    assert read_archive_ids(archive) == {"abc123", "def456", "999"}


def test_read_archive_ids_on_a_missing_file_is_empty(tmp_path):
    assert read_archive_ids(tmp_path / "nope.txt") == set()


def test_merge_unions_shards_after_existing_lines_without_duplicates(tmp_path):
    main = tmp_path / "main.txt"
    main.write_text("youtube old1\nyoutube dup\n", encoding="utf-8")
    shard = tmp_path / "shard-0.txt"
    shard.write_text("youtube dup\nyoutube new1\n", encoding="utf-8")
    dest = tmp_path / "merged.txt"
    merge_archives([shard], main, dest)
    assert dest.read_text(encoding="utf-8").splitlines() == [
        "youtube old1",
        "youtube dup",
        "youtube new1",
    ]


def test_merge_creates_a_missing_destination(tmp_path):
    shard = tmp_path / "shard-0.txt"
    shard.write_text("youtube new1\n", encoding="utf-8")
    dest = tmp_path / "sub" / "merged.txt"
    merge_archives([shard], tmp_path / "no-main.txt", dest)
    assert dest.read_text(encoding="utf-8").splitlines() == ["youtube new1"]
