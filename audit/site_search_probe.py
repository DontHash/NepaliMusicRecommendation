"""Probe: can the lyric sites' search endpoints cover the audio gap tracks?"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import requests
from rapidfuzz import fuzz

ROOT = Path(r"D:\Code\ProjectR")
sys.path.insert(0, str(ROOT))

from scripts.audio import utils  # noqa: E402

HEADERS = {"User-Agent": "ProjectR-research/0.2 (Nepali lyrics corpus; local research project)"}
WORDPRESS = [
    ("paankopat", "https://paankopat.com"),
    ("nepaligeetlyrics", "https://nepaligeetlyrics.com"),
]
BLOGGER = [
    ("nepali-songslyrics", "https://www.nepali-songslyrics.com"),
    ("geetishabda", "https://geetishabda.blogspot.com"),
]

session = requests.Session()
session.headers.update(HEADERS)


def track_sample(n: int = 6) -> list[dict]:
    rows = list(csv.DictReader(open(ROOT / "R_data" / "audio" / "audio_tracks.csv", encoding="utf-8")))
    done = {json.loads(line)["track_key"] for line in open(ROOT / "R_data" / "audio" / "audio_lyrics.jsonl", encoding="utf-8") if line.strip()}
    gaps = [r for r in rows if r["track_key"] not in done and r["metadata_match"] == "probable" and float(r["artist_score"] or 0) >= 85]
    return gaps[:n]


def wp_search(base: str, query: str) -> list[dict]:
    try:
        response = session.get(f"{base}/wp-json/wp/v2/posts", params={"search": query, "per_page": 5, "_fields": "id,link,title"}, timeout=25)
        if response.status_code != 200:
            return [{"error": response.status_code}]
        return response.json()
    except Exception as error:  # noqa: BLE001
        return [{"error": str(error)[:80]}]


def blogger_search(base: str, query: str) -> list[dict]:
    try:
        response = session.get(f"{base}/feeds/posts/default", params={"alt": "json", "q": query, "max-results": 5}, timeout=25)
        if response.status_code != 200:
            return [{"error": response.status_code}]
        entries = response.json().get("feed", {}).get("entry", [])
        return [{"title": e.get("title", {}).get("$t", ""), "link": (e.get("link") or [{}])[-1].get("href", "")} for e in entries]
    except Exception as error:  # noqa: BLE001
        return [{"error": str(error)[:80]}]


def main() -> None:
    for _, base in WORDPRESS + BLOGGER:
        try:
            robots = session.get(f"{base}/robots.txt", timeout=15)
            allow = "DISALLOW" if "Disallow: /" in robots.text else "ok"
            bad = [line for line in robots.text.splitlines() if line.lower().startswith("disallow") and ("search" in line or "api" in line or "wp-json" in line)]
            print(f"[robots] {base} -> {allow} {bad}")
        except Exception as error:  # noqa: BLE001
            print(f"[robots] {base} ERROR {error}")

    print()
    for track in track_sample():
        title = utils.strip_junk(track["title"]).strip()
        artist = utils.primary_artist(track["artist"]).strip()
        query = f"{title} {artist}".strip()
        print(f"### {artist} - {title}")
        for name, base in WORDPRESS:
            results = wp_search(base, query)
            if results and "error" in results[0]:
                print(f"  {name:20s} error={results[0]['error']}")
                continue
            scored = sorted(
                ((fuzz.token_set_ratio(utils.normalize_text(title), utils.normalize_text(str(r.get("title", {}).get("rendered", "")))), r) for r in results),
                reverse=True,
            )
            top = scored[0] if scored else None
            print(f"  {name:20s} hits={len(results)} best={top[0]:.0f} {str(top[1].get('title', {}).get('rendered', ''))[:70]!r}" if top else f"  {name:20s} hits=0")
        for name, base in BLOGGER:
            results = blogger_search(base, query)
            if results and "error" in results[0]:
                print(f"  {name:20s} error={results[0]['error']}")
                continue
            scored = sorted(
                ((fuzz.token_set_ratio(utils.normalize_text(title), utils.normalize_text(str(r.get("title", "")))), r) for r in results),
                reverse=True,
            )
            top = scored[0] if scored else None
            print(f"  {name:20s} hits={len(results)} best={top[0]:.0f} {str(top[1].get('title', ''))[:70]!r}" if top else f"  {name:20s} hits=0")
        print()


if __name__ == "__main__":
    main()
