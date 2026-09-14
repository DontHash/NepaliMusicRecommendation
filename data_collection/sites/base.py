"""Shared helpers for lyric-site adapters."""

from __future__ import annotations

import re
from dataclasses import dataclass

CHORD_TOKEN_RE = re.compile(
    r"^[A-G](#|b)?(m|maj|min|dim|aug|sus|add|no|°)?\d*(\/[A-G](#|b)?)?$",
    re.IGNORECASE,
)
MAX_CHORD_LINE_TOKENS = 10
MAX_CHORD_LINE_CHARS = 40
SKIP_LINE_MARKERS = ("⚠ unverified", "📖 read in devanagari", "read in devanagari")


@dataclass(slots=True)
class SongPage:
    artist: str
    title: str
    lyrics: str


def _is_chord_line(line: str) -> bool:
    tokens = [token.strip(".,;|()[]") for token in line.replace("|", " ").split()]
    tokens = [token for token in tokens if token]
    if not tokens or len(tokens) > MAX_CHORD_LINE_TOKENS or len(line) > MAX_CHORD_LINE_CHARS:
        return False
    return all(CHORD_TOKEN_RE.match(token) for token in tokens)


def strip_chord_lines(text: str) -> str:
    kept: list[str] = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.casefold() in SKIP_LINE_MARKERS:
            continue
        if _is_chord_line(stripped):
            continue
        kept.append(line.rstrip())
    return "\n".join(kept).strip()
