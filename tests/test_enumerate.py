"""Tests for shiori.runner.enumerate — listing a tab's video IDs."""
from shiori.runner.enumerate import list_tab_ids


def test_list_tab_ids_parses_one_id_per_line_and_drops_blanks():
    def fake_run(argv, **kwargs):
        class Completed:
            returncode = 0
            stdout = "aaa\n\nNA\nbbb\n"
            stderr = ""
        return Completed()

    assert list_tab_ids("yt-dlp", "https://x/videos", run=fake_run) == ["aaa", "bbb"]


def test_list_tab_ids_sends_flat_playlist_id_print():
    seen = {}

    def fake_run(argv, **kwargs):
        seen["argv"] = argv

        class Completed:
            returncode = 0
            stdout = ""
            stderr = ""
        return Completed()

    list_tab_ids("yt-dlp", "https://x/videos", run=fake_run)
    assert "--flat-playlist" in seen["argv"]
    assert seen["argv"][seen["argv"].index("--print") + 1] == "%(id)s"
    assert seen["argv"][-1] == "https://x/videos"
