"""Data model for candidates, lyrics hits, and fetch outcomes."""

from __future__ import annotations

from dataclasses import dataclass, field

from .normalize import make_dedupe_key

OUTCOME_HIT = "hit"
OUTCOME_MISS = "miss"
OUTCOME_ERROR = "error"


@dataclass(slots=True)
class Candidate:
    source: str
    artist: str
    title: str
    source_id: str | None = None
    album: str | None = None
    duration_s: int | None = None
    preview_url: str | None = None
    isrc: str | None = None
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def dedupe_key(self) -> str:
        return make_dedupe_key(self.artist, self.title, self.duration_s)


@dataclass(slots=True)
class LyricsHit:
    stage: str
    lyrics: str
    source_url: str | None = None
    synced: bool = False
    script: str = "unknown"
    sha256: str = ""
