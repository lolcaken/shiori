"""Tests for akari.runner.progress — typed events parsed from yt-dlp output."""
from akari.runner.progress import (
    ErrorLine,
    FileStart,
    Ignored,
    MergeStart,
    Progress,
    Skipped,
    WarningLine,
    parse_line,
)


def test_progress_update_parses_percent_total_speed_eta():
    event = parse_line("[download]  54.7% of  107.26MiB at   20.58MiB/s ETA 00:02")
    assert event == Progress(percent=54.7, total="107.26MiB", speed="20.58MiB/s", eta="00:02")
    assert event.done is False


def test_unknown_speed_and_eta_become_none():
    event = parse_line("[download]  63.9% of  107.26MiB at  Unknown B/s ETA Unknown")
    assert event == Progress(percent=63.9, total="107.26MiB", speed=None, eta=None)


def test_completion_line_is_a_done_progress_event():
    event = parse_line("[download] 100% of  10.00MiB in 00:01 at  9.00MiB/s")
    assert isinstance(event, Progress)
    assert event.done is True


def test_destination_line_starts_a_file():
    event = parse_line("[download] Destination: some/dir/video.mp4")
    assert event == FileStart(path="some/dir/video.mp4")


def test_merger_line_announces_the_final_file():
    event = parse_line('[Merger] Merging formats into "some/movie [en].mp4"')
    assert event == MergeStart(path="some/movie [en].mp4")


def test_already_downloaded_is_a_skip():
    event = parse_line("[download] some/dir/video.mp4 has already been downloaded")
    assert event == Skipped(path="some/dir/video.mp4")


def test_archive_recorded_is_a_skip():
    event = parse_line("[download] abc123 has already been recorded in the archive")
    assert event == Skipped(path="abc123")


def test_error_line_is_surfaced():
    event = parse_line("ERROR: [youtube] 123: Private video")
    assert event == ErrorLine(text="[youtube] 123: Private video")


def test_warning_line_is_counted():
    event = parse_line("WARNING: No subtitles found for video")
    assert event == WarningLine(text="No subtitles found for video")


def test_extraction_chatter_and_postprocessing_are_ignored():
    assert isinstance(parse_line("[youtube] abc: Downloading webpage"), Ignored)
    assert isinstance(
        parse_line('[VideoRemuxer] Not remuxing media file "x.mp4"'), Ignored
    )
    assert isinstance(parse_line("[EmbedSubtitle] Embedding subtitles"), Ignored)
    assert isinstance(parse_line(""), Ignored)


def test_describe_renders_a_compact_status():
    assert (
        Progress(54.7, "107.26MiB", "20.58MiB/s", "00:02").describe()
        == "54.7% of 107.26MiB at 20.58MiB/s ETA 00:02"
    )
    assert (
        Progress(63.9, "107.26MiB", None, None).describe()
        == "63.9% of 107.26MiB"
    )
