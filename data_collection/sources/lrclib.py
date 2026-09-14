"""LRCLIB lyrics client (free, no API key required)."""

from __future__ import annotations

import re

from rapidfuzz import fuzz

from ..http import CachedHttp
from ..models import LyricsHit
from ..normalize import detect_script, lyrics_sha

BASE = "https://lrclib.net/api"
SOURCE = "lrclib"
LRC_LINE_RE = re.compile(r"^\[\d{1,2}:\d{2}(?:\.\d{1,3})?\]\s?")
TITLE_MATCH_THRESHOLD = 75
MAX_DURATION_DIFF = 20


def strip_lrc(text: str) -> str:
    lines = [LRC_LINE_RE.sub("", line).strip() for line in (text or "").splitlines()]
    return "\n".join(line for line in lines if line).strip()


def get_lyrics(client: CachedHttp, *, artist: str, title: str, album: str | None = None, duration: int | None = None) -> dict | None:
    params = {"artist_name": artist, "track_name": title}
    if album:
        params["album_name"] = album
    if duration:
        params["duration"] = int(duration)
    result = client.get_json(SOURCE, f"{BASE}/get", params)
    if result.ok and isinstance(result.data, dict) and result.data.get("trackName"):
        return result.data
    return None


def search_lyrics(client: CachedHttp, *, artist: str | None = None, title: str | None = None, query: str | None = None) -> list[dict]:
    params: dict = {}
    if query:
        params["q"] = query
    else:
        if title:
            params["track_name"] = title
        if artist:
            params["artist_name"] = artist
    if not params:
        return []
    result = client.get_json(SOURCE, f"{BASE}/search", params)
    if result.ok and isinstance(result.data, list):
        return result.data
    return []


def pick_best(records: list[dict], *, duration: int | None = None, artist: str | None = None, title: str | None = None) -> dict | None:
    best = None
    best_score = None
    for record in records:
        if not (record.get("plainLyrics") or record.get("syncedLyrics")):
            continue
        score = 0.0
        if title:
            score += fuzz.token_set_ratio(title.casefold(), str(record.get("trackName") or "").casefold())
        if artist:
            score += fuzz.token_set_ratio(artist.casefold(), str(record.get("artistName") or "").casefold())
        if duration and record.get("duration"):
            diff = abs(int(record["duration"]) - int(duration))
            if diff > MAX_DURATION_DIFF:
                continue
            score -= diff
        if best_score is None or score > best_score:
            best, best_score = record, score
    if best is None:
        return None
    if title and fuzz.token_set_ratio(title.casefold(), str(best.get("trackName") or "").casefold()) < TITLE_MATCH_THRESHOLD:
        return None
    return best


def record_to_hit(record: dict, *, stage: str = "lrclib") -> LyricsHit | None:
    plain = str(record.get("plainLyrics") or "").strip()
    synced = str(record.get("syncedLyrics") or "").strip()
    if not plain and synced:
        plain = strip_lrc(synced)
    if not plain:
        return None
    record_id = record.get("id")
    url = f"https://lrclib.net/api/get/{record_id}" if record_id is not None else None
    return LyricsHit(
        stage=stage,
        lyrics=plain,
        source_url=url,
        synced=bool(synced),
        script=detect_script(plain),
        sha256=lyrics_sha(plain),
    )
