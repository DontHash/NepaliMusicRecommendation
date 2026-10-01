"""Diagnostic: direct LRCLIB probe for well-known Nepali tracks + manifest sample."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import requests

ROOT = Path(r"D:\Code\ProjectR")
sys.path.insert(0, str(ROOT))

HEADERS = {"User-Agent": "ProjectR-research/0.2 (Nepali lyrics corpus; local research project)"}

TESTS = [
    ("Narayan Gopal", "Euta Manche Ko Mayale"),
    ("Narayan Gopal", "Malai Nasodha"),
    ("Bipul Chettri", "Wildfire"),
    ("Bipul Chettri", "Deorali Darah"),
    ("Sushant KC", "Sarangi"),
    ("Yama Buddha", "Saathi"),
    ("Kunti Moktan", "Uhi Chalaki"),
    ("Nabin K Bhattarai", "Sannani"),
    ("Sabin Rai", "Komal Tyo Timro"),
    ("1974 AD", "Nepali Ho"),
]

session = requests.Session()
session.headers.update(HEADERS)

print("=== direct /api/get ===")
for artist, title in TESTS:
    try:
        response = session.get("https://lrclib.net/api/get", params={"artist_name": artist, "track_name": title}, timeout=20)
        if response.status_code == 200:
            data = response.json()
            has = bool(data.get("plainLyrics") or data.get("syncedLyrics"))
            print(f"200 lyrics={has} | {artist} - {title}")
        else:
            print(f"{response.status_code} | {artist} - {title}")
            search = session.get("https://lrclib.net/api/search", params={"track_name": title, "artist_name": artist}, timeout=20)
            hits = search.json() if search.status_code == 200 else []
            with_lyrics = sum(1 for hit in hits if hit.get("plainLyrics") or hit.get("syncedLyrics"))
            print(f"    search {search.status_code} hits={len(hits)} with_lyrics={with_lyrics}")
            if hits:
                print(f"    first: {hits[0].get('artistName')!r} - {hits[0].get('trackName')!r}")
    except Exception as error:  # noqa: BLE001
        print("ERROR", artist, title, error)

print("\n=== random manifest sample (probable, non-generic) ===")
rows = list(csv.DictReader(open(ROOT / "R_data" / "audio" / "audio_tracks.csv", encoding="utf-8")))
import random

random.seed(7)
sample = [r for r in rows if r["metadata_match"] in {"probable", "weak"}]
random.shuffle(sample)
for row in sample[:10]:
    artist = row["artist"].split(",")[0].split("&")[0].split(" feat")[0].strip()
    title = row["title"]
    try:
        response = session.get("https://lrclib.net/api/get", params={"artist_name": artist, "track_name": title}, timeout=20)
        if response.status_code == 200:
            data = response.json()
            has = bool(data.get("plainLyrics") or data.get("syncedLyrics"))
            print(f"200 lyrics={has} | {artist} - {title}")
        else:
            print(f"{response.status_code} | {artist} - {title} | query={row['source_query'][:30]}")
    except Exception as error:  # noqa: BLE001
        print("ERROR", artist, title, error)
