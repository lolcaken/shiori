"""Parse yt-dlp's stdout into typed events so logging stays organized.

yt-dlp is chatty (one progress line per update, extraction chatter,
postprocessor notes). The parser distills each line into exactly one
event; runner/process.py decides what reaches the terminal.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_PROGRESS = re.compile(
    r"^\[download\]\s+(\d+(?:\.\d+)?)% of\s+(\S+)"
    r"(?:\s+at\s+(\S+))?(?:\s+ETA\s+(\S+))?"
)
_DESTINATION = re.compile(r"^\[download\] Destination: (.+)$")
_MERGE = re.compile(r'^\[Merger\] Merging formats into "(.+)"$')
_SKIPPED = re.compile(
    r"^(?:\[download\] )?(.+) has already been "
    r"(downloaded(?: and merged)?|recorded in the archive)$"
)
_ERROR = re.compile(r"^ERROR:\s?(.*)$")
_WARNING = re.compile(r"^WARNING:\s?(.*)$")


@dataclass(frozen=True)
class Progress:
    percent: float
    total: str | None
    speed: str | None
    eta: str | None

    @property
    def done(self) -> bool:
        return self.percent >= 100

    def describe(self) -> str:
        text = f"{self.percent:g}% of {self.total}"
        if self.speed:
            text += f" at {self.speed}"
        if self.eta:
            text += f" ETA {self.eta}"
        return text


@dataclass(frozen=True)
class FileStart:
    path: str


@dataclass(frozen=True)
class MergeStart:
    path: str


@dataclass(frozen=True)
class Skipped:
    path: str


@dataclass(frozen=True)
class ErrorLine:
    text: str


@dataclass(frozen=True)
class WarningLine:
    text: str


@dataclass(frozen=True)
class Ignored:
    pass


def _clean(value: str | None) -> str | None:
    if value is None or value.startswith("Unknown"):
        return None
    return value


def parse_line(line: str):
    """Return the single event a raw yt-dlp output line represents."""
    line = line.rstrip("\n")
    match = _DESTINATION.match(line)
    if match:
        return FileStart(path=match.group(1).strip())
    match = _MERGE.match(line)
    if match:
        return MergeStart(path=match.group(1).strip())
    match = _SKIPPED.match(line)
    if match:
        return Skipped(path=match.group(1).strip())
    match = _PROGRESS.match(line)
    if match:
        return Progress(
            percent=float(match.group(1)),
            total=match.group(2),
            speed=_clean(match.group(3)),
            eta=_clean(match.group(4)),
        )
    match = _ERROR.match(line)
    if match:
        return ErrorLine(text=match.group(1))
    match = _WARNING.match(line)
    if match:
        return WarningLine(text=match.group(1))
    return Ignored()
