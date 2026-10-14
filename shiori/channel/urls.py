"""Normalizing user-supplied channel URLs and building per-tab URLs."""
from __future__ import annotations

from urllib.parse import urlparse

from shiori.channel.tabs import TAB_SPECS, spec_for
from shiori.core.errors import UsageError
from shiori.core.models import Tab

_KNOWN_TAB_SUFFIXES = tuple(f"/{spec.url_suffix}" for spec in TAB_SPECS.values())


def normalize_channel_url(raw: str) -> str:
    """Turn user input into a canonical channel URL without a tab suffix.

    Accepts full channel URLs and bare ``@handle`` shorthand.
    """
    text = (raw or "").strip()
    if not text:
        raise UsageError("channel URL must not be empty")
    if text.startswith("@"):
        text = f"https://www.youtube.com/{text}"

    parsed = urlparse(text)
    if not parsed.scheme or "youtube.com" not in (parsed.netloc or ""):
        raise UsageError(f"not a YouTube channel URL: {raw!r}")
    if parsed.path.startswith("/watch"):
        raise UsageError(f"not a channel URL (looks like a single video): {raw!r}")

    text = text.rstrip("/")
    for suffix in _KNOWN_TAB_SUFFIXES:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    return text.rstrip("/")


def tab_url(channel_url: str, tab: Tab) -> str:
    return f"{channel_url}/{spec_for(tab).url_suffix}"
