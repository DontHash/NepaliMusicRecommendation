"""High-confidence coverage of the corpus and mood-gold by the audio collection."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Code\ProjectR")
MATCH_CSV = ROOT / "audit" / "audio_match.csv"          # filename-based best match per file (score >= 60)
SUMMARY_OUT = ROOT / "audit" / "audio_corpus_coverage.json"


def main() -> None:
    by_song: dict[int, float] = {}
    with open(MATCH_CSV, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if not row["song_id"]:
                continue
            sid = int(row["song_id"])
            score = float(row["score"])
            by_song[sid] = max(by_song.get(sid, 0.0), score)

    gold = {}
    with open(ROOT / "eval" / "mood_gold.csv", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            gold[int(row["song_id"])] = row

    corpus = []
    with open(ROOT / "music_rec_artifacts" / "cleaned_lyrics.csv", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            corpus.append(row)

    def bucket(thresh: float) -> set[int]:
        return {sid for sid, score in by_song.items() if score >= thresh}

    strong, probable, weak = bucket(92), bucket(82), bucket(70)
    gold_ids = set(gold)
    corpus_ids = {int(r["song_id"]) for r in corpus}

    summary = {
        "corpus_songs": len(corpus_ids),
        "covered_strong_92": len(strong & corpus_ids),
        "covered_probable_82": len(probable & corpus_ids),
        "covered_weak_70": len(weak & corpus_ids),
        "gold_songs": len(gold_ids),
        "gold_with_audio_strong_92": len(strong & gold_ids),
        "gold_with_audio_probable_82": len(probable & gold_ids),
        "gold_with_audio_weak_70": len(weak & gold_ids),
        "gold_missing_all_audio": sorted(gold_ids - weak),
    }
    print(json.dumps(summary, indent=2))
    with open(SUMMARY_OUT, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    # artist coverage
    artist_of = {int(r["song_id"]): r["artist"] for r in corpus}
    from collections import Counter

    artists_strong = Counter(artist_of[sid] for sid in strong & corpus_ids)
    print("\ntop artists covered (strong >=92):")
    for artist, count in artists_strong.most_common(15):
        print(f"  {count:4d}  {artist}")


if __name__ == "__main__":
    main()
