"""Sanitize an arbitrary display name into a safe single path segment."""
from __future__ import annotations

import re

from shiori.core.errors import UsageError

_ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_folder_name(name: str) -> str:
    """Replace filesystem-illegal characters so the name is safe on Windows."""
    cleaned = _ILLEGAL.sub("_", (name or "").strip())
    cleaned = cleaned.rstrip(". ")
    if not cleaned:
        raise UsageError("channel name sanitizes to an empty folder name")
    return cleaned
