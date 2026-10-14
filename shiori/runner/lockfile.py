"""One archiver per channel folder.

Two shiori processes writing one archive file interleave lines and
corrupt it. The lock file holds the owner's PID; a lock whose process
is gone (or unreadable) is stale and gets taken over. Released only by
its owner, in a ``finally`` — a killed run leaves the lock behind, and
the next run correctly treats it as stale.
"""
from __future__ import annotations

import os
from pathlib import Path

from shiori.core.errors import ShioriError

LOCK_NAME = ".shiori-lock"


def pid_alive(pid: int) -> bool:
    """True if a process with this PID exists right now. Never raises."""
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes

            handle = ctypes.windll.kernel32.OpenProcess(0x00100000, False, pid)
            if not handle:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ValueError, OverflowError):
        return False


def _read_pid(lock: Path) -> int | None:
    try:
        return int(lock.read_text(encoding="utf-8").split()[0])
    except (OSError, ValueError, IndexError):
        return None


def acquire_lock(channel_dir: Path) -> Path:
    """Claim the channel folder or raise ShioriError if someone holds it."""
    channel_dir.mkdir(parents=True, exist_ok=True)
    lock = channel_dir / LOCK_NAME
    if lock.is_file():
        old_pid = _read_pid(lock)
        if old_pid is not None and pid_alive(old_pid):
            raise ShioriError(
                f"another shiori run (pid {old_pid}) is archiving this channel"
            )
    lock.write_text(f"{os.getpid()}\n", encoding="utf-8")
    return lock


def release_lock(lock: Path) -> None:
    """Remove the lock, but only if it is still ours."""
    try:
        if lock.is_file() and _read_pid(lock) == os.getpid():
            lock.unlink()
    except OSError:
        pass
