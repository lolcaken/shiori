"""Tests for shiori.runner.scratch — subtitle temp dir lifecycle."""


from shiori.runner.scratch import scratch_dir


def test_scratch_dir_exists_inside_and_is_removed_after():
    with scratch_dir() as tmp:
        assert tmp.is_dir()
        (tmp / "a.en.vtt").write_text("WEBVTT\n")
    assert not tmp.exists()


def test_scratch_dir_takes_a_prefix_for_recognizability(tmp_path):
    with scratch_dir(prefix="shiori-test-") as tmp:
        assert tmp.name.startswith("shiori-test-")
