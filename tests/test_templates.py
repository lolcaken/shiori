"""Tests for akari.naming.templates — the yt-dlp -o filename template."""


from akari.naming.templates import video_filename_template


def test_template_carries_date_title_tag_and_extension():
    template = video_filename_template("en")
    assert "%(upload_date>%Y-%m-%d" in template
    assert "%(title)s" in template
    assert "[en]" in template
    assert template.endswith(".%(ext)s")


def test_livestreams_without_upload_date_fall_back_to_release_date():
    template = video_filename_template("en")
    assert "release_date" in template


def test_empty_tag_means_no_brackets():
    template = video_filename_template("")
    assert "[" not in template
    assert "]" not in template
