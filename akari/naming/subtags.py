"""Derive the [lang] filename tag from the --sub-langs selection."""
from __future__ import annotations

import re

_CLEAN = re.compile(r"[^A-Za-z0-9_-]+")


def subtitle_tag(sub_langs: str) -> str:
    """Turn a --sub-langs value into a deterministic filename tag.

    ``en.*`` -> ``en``; ``en.*,ja`` -> ``en-ja``; ``all`` -> ``""``
    because the embedded languages are unknowable up front.
    """
    tokens = [t.strip() for t in (sub_langs or "").split(",")]
    included = [t for t in tokens if t and not t.startswith("-")]
    if not included or included == ["all"]:
        return ""
    cleaned = [_CLEAN.sub("", token) for token in included]
    return "-".join(part for part in cleaned if part)
