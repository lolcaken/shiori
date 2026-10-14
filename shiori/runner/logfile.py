"""Mirror console output to a per-run log file without the progress spam.

Live ``\\r`` status lines would fill the file with hundreds of
near-identical lines, so only the final state of each ``\\r`` run (the
text after the last carriage return before the newline) is written.
"""
from __future__ import annotations

import contextlib
import sys
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import IO


class TeeWriter:
    """Write everything to the console; write only final lines to the file."""

    def __init__(self, console, handle: IO[str]) -> None:
        self._console = console
        self._handle = handle
        self._buf = ""

    def write(self, text: str) -> int:
        self._console.write(text)
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            final = line.rsplit("\r", 1)[-1]
            if final.strip():
                self._handle.write(final + "\n")
        return len(text)

    def flush(self) -> None:
        self._console.flush()
        self._handle.flush()

    def isatty(self) -> bool:
        return self._console.isatty()

    def close(self) -> None:
        final = self._buf.rsplit("\r", 1)[-1]
        if final.strip():
            self._handle.write(final + "\n")
        self._buf = ""
        self.flush()
        self._handle.close()


@contextlib.contextmanager
def log_session(log_dir: Path) -> Iterator:
    """Mirror stdout into ``<log_dir>/<timestamp>.log`` for the wrapped block.

    Falls back to plain console output (with a stderr warning) when the
    log directory cannot be created — logging must never break a run.
    """
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        handle = (log_dir / f"{stamp}.log").open("w", encoding="utf-8")
    except OSError as exc:
        print(f"shiori: warning: logging disabled ({exc})", file=sys.stderr)
        yield sys.stdout
        return
    tee = TeeWriter(sys.stdout, handle)
    try:
        with contextlib.redirect_stdout(tee):
            yield tee
    finally:
        tee.close()
