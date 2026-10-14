"""Tests for akari.planner.flag_sets — argv grouped by concern."""
from pathlib import Path

from akari.planner import flag_sets


def test_format_flags_request_mp4():
    flags = flag_sets.format_flags()
    assert flags == ["-t", "mp4"]


def test_subtitle_output_flags_point_at_an_exact_scratch_template():
    flags = flag_sets.subtitle_output_flags(Path("/tmp/subs"))
    template = flags[flags.index("-o") + 1]
    assert template.startswith("subtitle:")
    assert "/tmp/subs" in template.replace("\\", "/")
    assert template.endswith("%(title)s.%(ext)s")


def test_subtitle_flags_fetch_real_and_auto_subs_and_embed_them():
    flags = flag_sets.subtitle_flags("en.*")
    for expected in ("--write-subs", "--write-auto-subs", "--embed-subs"):
        assert expected in flags
    assert flags[flags.index("--sub-langs") + 1] == "en.*"
    assert "--keep-subs" not in " ".join(flags)  # mp4-only: no .vtt left behind


def test_resume_flags_use_the_download_archive_by_default():
    flags = flag_sets.resume_flags(Path("archives/Chan/.akari-archive.txt"), full=False)
    assert flags[flags.index("--download-archive") + 1].endswith(".akari-archive.txt")
    assert "--continue" in flags
    assert "--no-overwrites" in flags


def test_resume_flags_skip_the_archive_for_a_full_rebuild():
    assert "--download-archive" not in flag_sets.resume_flags(Path("x"), full=True)


def test_network_flags_carry_jobs_and_sleep():
    assert flag_sets.network_flags(jobs=4, sleep_interval=2.0) == [
        "-N", "4", "--sleep-interval", "2.0",
    ]


def test_filesystem_flags_keep_filenames_windows_safe_and_bounded():
    flags = flag_sets.filesystem_flags()
    assert "--windows-filenames" in flags
    assert flags[flags.index("--trim-filenames") + 1] == "180"


def test_metadata_flags_embed_metadata_and_cover_art():
    flags = flag_sets.metadata_flags()
    assert "--embed-metadata" in flags
    assert "--embed-thumbnail" in flags


def test_date_flags_are_empty_without_a_range():
    assert flag_sets.date_flags(None, None) == []


def test_date_flags_map_since_until_to_dateafter_datebefore():
    assert flag_sets.date_flags("20240101", "20241231") == [
        "--dateafter", "20240101", "--datebefore", "20241231",
    ]
