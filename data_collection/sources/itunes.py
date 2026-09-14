"""iTunes Search API enumeration (no API key required)."""

from __future__ import annotations

from ..http import CachedHttp
from ..models import Candidate

BASE = "https://itunes.apple.com"
SOURCE = "itunes"


def search_songs(client: CachedHttp, term: str, limit: int = 200, country: str = "US") -> list[dict]:
    result = client.get_json(
        SOURCE,
        f"{BASE}/search",
        {"term": term, "entity": "song", "limit": limit, "country": country},
    )
    if not result.ok or not isinstance(result.data, dict):
        return []
    return result.data.get("results") or []


def track_to_candidate(track: dict) -> Candidate | None:
    title = str(track.get("trackName") or "").strip()
    if not title:
        return None
    duration_ms = track.get("trackTimeMillis")
    duration = int(round(duration_ms / 1000)) if isinstance(duration_ms, (int, float)) and duration_ms > 0 else None
    return Candidate(
        source=SOURCE,
        source_id=str(track.get("trackId")) if track.get("trackId") is not None else None,
        artist=str(track.get("artistName") or "").strip(),
        title=title,
        album=str(track.get("collectionName") or "").strip() or None,
        duration_s=duration,
        preview_url=str(track.get("previewUrl")) if track.get("previewUrl") else None,
    )
