"""ANSI highlighting for the download log.

The per-update progress spam is back by popular demand — dressed up:
percent in bold cyan, size in yellow, speed in green, ETA in magenta.
Colors only ever reach a live terminal; pipes, files and `--no-color`
keep the plain collapsed output.
"""
from __future__ import annotations

import os
import sys

from shiori.runner.progress import Progress

BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
MAGENTA = "\033[35m"
RESET = "\033[0m"


def colorize_progress(event: Progress, trailing: str = "") -> str:
    """Render one `[download]` update line with ANSI highlights."""
    parts = [
        f"{DIM}[download]{RESET}",
        f" {BOLD}{CYAN}{event.percent:g}%{RESET}",
        f" of {YELLOW}{event.total}{RESET}",
    ]
    if event.speed:
        parts.append(f" at {GREEN}{event.speed}{RESET}")
    if event.eta:
        parts.append(f" ETA {MAGENTA}{event.eta}{RESET}")
    if trailing:
        parts.append(f" -- {trailing}")
    return "".join(parts)


def use_color(no_color: bool) -> bool:
    """Colors only on a live terminal, unless disabled by flag or env."""
    if no_color or os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def enable_vt() -> None:
    """Best-effort: switch the Windows console to ANSI mode. Never raises."""
    if os.name != "nt":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass
