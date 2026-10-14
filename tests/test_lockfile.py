"""Tests for shiori.runner.lockfile — one archiver per channel folder."""
import os

import pytest

from shiori.core.errors import ShioriError
from shiori.runner.lockfile import acquire_lock, pid_alive, release_lock


def test_own_pid_is_alive_but_absurd_pids_are_not():
    assert pid_alive(os.getpid()) is True
    assert pid_alive(2**30) is False
    assert pid_alive(-5) is False


def test_second_acquire_while_held_is_refused(tmp_path):
    acquire_lock(tmp_path)
    with pytest.raises(ShioriError):
        acquire_lock(tmp_path)


def test_stale_and_garbled_locks_are_taken_over(tmp_path):
    (tmp_path / ".shiori-lock").write_text("999999999\n", encoding="utf-8")
    acquire_lock(tmp_path)
    (tmp_path / ".shiori-lock").write_text("not-a-pid\n", encoding="utf-8")
    acquire_lock(tmp_path)


def test_release_removes_only_our_own_lock(tmp_path):
    lock = acquire_lock(tmp_path)
    release_lock(lock)
    assert not lock.exists()
    foreign = tmp_path / ".shiori-lock"
    foreign.write_text("999999999\n", encoding="utf-8")
    release_lock(foreign)
    assert foreign.is_file()
