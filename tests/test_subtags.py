"""Tests for akari.naming.subtags — the [lang] tag derived from --sub-langs."""


from akari.naming.subtags import subtitle_tag


def test_regex_suffix_is_cleaned_off():
    assert subtitle_tag("en.*") == "en"


def test_multiple_languages_are_joined():
    assert subtitle_tag("en.*,ja") == "en-ja"


def test_all_means_no_tag_because_languages_are_unknown():
    assert subtitle_tag("all") == ""


def test_exclusion_patterns_are_ignored():
    assert subtitle_tag("en.*,-live_chat") == "en"
