"""Interactive / scripted demo for the music recommender."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from music_rec.recommender import MusicRecommender


def _print(recs, header):
    print(f"\n=== {header} ===")
    if not recs:
        print("  (no results)")
        return
    for i, r in enumerate(recs, 1):
        sent = f" sentiment={r.sentiment_score:+.2f}" if r.sentiment_score is not None else ""
        print(f"  {i:2d}. [{r.song_id}] {r.title} — {r.artist}  (score={r.score}{sent})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", type=str, default=None, help="Free-text / Romanized query")
    parser.add_argument("--song-id", type=int, default=None, help="Seed song id")
    parser.add_argument("--artist", type=str, default=None, help="Hard filter by artist")
    parser.add_argument("--category", type=str, default=None, help="Hard filter by category")
    args = parser.parse_args()

    rec = MusicRecommender.load()

    if args.text:
        normalized = rec.normalized_query(args.text)
        print(f"Query: {args.text!r} -> normalized: {normalized!r}")
        _print(
            rec.recommend_by_text(args.text, artist=args.artist, category=args.category),
            f"Free-text recommendations for {args.text!r}",
        )
    elif args.song_id is not None:
        seed = rec.songs.loc[args.song_id]
        print(f"Seed: [{args.song_id}] {seed['title']} — {seed['artist']}")
        _print(
            rec.recommend_by_song(args.song_id, artist=args.artist, category=args.category),
            "Similar songs",
        )
    else:
        # Default showcase.
        for q in ["maya", "dukha ko geet", "nepali"]:
            normalized = rec.normalized_query(q)
            print(f"\nQuery: {q!r} -> normalized: {normalized!r}")
            _print(rec.recommend_by_text(q), f"Free-text recommendations for {q!r}")
        _print(rec.recommend_by_song(0), "Similar to song 0")


if __name__ == "__main__":
    main()
