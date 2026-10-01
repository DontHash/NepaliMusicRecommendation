"""Audio-similarity diagnostics: nearest-neighbour stats + duplicate candidates.

Reads audio_embeddings.npy, writes R_data/audio/audio_duplicate_candidates.csv
(pairs with cosine >= threshold) and prints a summary.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audio import config, utils  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=float, default=0.99)
    parser.add_argument("--report-threshold", type=float, default=0.90)
    args = parser.parse_args()

    import numpy as np

    vectors = np.load(utils.AUDIO_DATA_DIR / "audio_embeddings.npy")
    with open(utils.AUDIO_DATA_DIR / "audio_embedding_keys.csv", encoding="utf-8") as handle:
        keys = [row["track_key"] for row in csv.DictReader(handle)]
    with open(utils.AUDIO_DATA_DIR / "audio_tracks.csv", encoding="utf-8") as handle:
        tracks = {row["track_key"]: row for row in csv.DictReader(handle)}
    links_path = utils.AUDIO_DATA_DIR / "audio_track_matches.csv"
    if links_path.exists():
        with open(links_path, encoding="utf-8") as handle:
            links = {row["track_key"]: row for row in csv.DictReader(handle)}
    else:
        links = {}

    vectors = vectors / np.clip(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-9, None)
    similarity = vectors @ vectors.T
    np.fill_diagonal(similarity, -1.0)
    nearest = similarity.argmax(axis=1)
    nearest_score = similarity[np.arange(len(nearest)), nearest]

    rows = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            score = float(similarity[i, j])
            if score >= args.threshold:
                a, b = tracks.get(keys[i], {}), tracks.get(keys[j], {})
                rows.append({
                    "score": round(score, 4),
                    "track_a": keys[i], "artist_a": a.get("artist", ""), "title_a": a.get("title", ""),
                    "song_a": links.get(keys[i], {}).get("match_song_id", "") or links.get(keys[i], {}).get("new_id", ""),
                    "track_b": keys[j], "artist_b": b.get("artist", ""), "title_b": b.get("title", ""),
                    "song_b": links.get(keys[j], {}).get("match_song_id", "") or links.get(keys[j], {}).get("new_id", ""),
                    "same_song": int(links.get(keys[i], {}).get("match_song_id", "") == links.get(keys[j], {}).get("match_song_id", "") != ""),
                })
    rows.sort(key=lambda row: -row["score"])
    out_path = utils.AUDIO_DATA_DIR / "audio_duplicate_candidates.csv"
    with open(out_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["score"])
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "schema_version": config.SCHEMA_VERSION,
        "vectors": len(keys),
        "threshold": args.threshold,
        "duplicate_pairs": len(rows),
        "tracks_with_nn_ge_0_95": int((nearest_score >= 0.95).sum()),
        "tracks_with_nn_ge_0_90": int((nearest_score >= 0.90).sum()),
        "median_nn": round(float(np.median(nearest_score)), 4),
        "nn_percentiles": {
            "p50": round(float(np.percentile(nearest_score, 50)), 4),
            "p90": round(float(np.percentile(nearest_score, 90)), 4),
            "p99": round(float(np.percentile(nearest_score, 99)), 4),
            "p99_9": round(float(np.percentile(nearest_score, 99.9)), 4),
        },
        "top_pairs": rows[:15],
    }
    (utils.AUDIO_DATA_DIR / "audio_similarity_report.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in summary.items() if k != "top_pairs"}, indent=2))
    print("top pairs:")
    for row in summary["top_pairs"]:
        print(f"  {row['score']:.3f}  {row['artist_a'][:20]} - {row['title_a'][:28]}  <->  {row['artist_b'][:20]} - {row['title_b'][:28]}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
