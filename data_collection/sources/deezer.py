"""Deezer catalog enumeration (no API key required)."""

from __future__ import annotations

from rapidfuzz import fuzz

from ..http import CachedHttp
from ..models import Candidate

BASE = "https://api.deezer.com"
SOURCE = "deezer"
MATCH_THRESHOLD = 80


def search_artists(client: CachedHttp, name: str, limit: int = 5) -> list[dict]:
    result = client.get_json(SOURCE, f"{BASE}/search/artist", {"q": name, "limit": limit})
    if not result.ok or not isinstance(result.data, dict):
        return []
    return result.data.get("data") or []


def best_artist_match(artists: list[dict], name: str) -> dict | None:
    best = None
    best_score = 0.0
    for artist in artists:
        candidate_name = str(artist.get("name") or "")
        score = fuzz.token_set_ratio(name.casefold(), candidate_name.casefold())
        if score > best_score:
            best, best_score = artist, score
    if best is None or best_score < MATCH_THRESHOLD:
        return None
    return best


def artist_albums(client: CachedHttp, artist_id: int | str, limit: int = 25) -> list[dict]:
    result = client.get_json(SOURCE, f"{BASE}/artist/{artist_id}/albums", {"limit": limit})
    if not result.ok or not isinstance(result.data, dict):
        return []
    return result.data.get("data") or []


def album_tracks(client: CachedHttp, album_id: int | str, limit: int = 100) -> list[dict]:
    result = client.get_json(SOURCE, f"{BASE}/album/{album_id}/tracks", {"limit": limit})
    if not result.ok or not isinstance(result.data, dict):
        return []
    return result.data.get("data") or []


def track_to_candidate(track: dict, *, album: str | None = None) -> Candidate | None:
    title = str(track.get("title") or track.get("title_short") or "").strip()
    if not title:
        return None
    artist = str((track.get("artist") or {}).get("name") or "").strip()
    duration = track.get("duration")
    return Candidate(
        source=SOURCE,
        source_id=str(track.get("id")) if track.get("id") is not None else None,
        artist=artist,
        title=title,
        album=album,
        duration_s=int(duration) if isinstance(duration, (int, float)) and duration > 0 else None,
        preview_url=str(track.get("preview")) if track.get("preview") else None,
        isrc=str(track.get("isrc")) if track.get("isrc") else None,
    )
