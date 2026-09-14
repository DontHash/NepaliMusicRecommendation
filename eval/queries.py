"""Build a graded query set from the cleaned corpus (objective + mood queries)."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLEANED = PROJECT_ROOT / "music_rec_artifacts" / "cleaned_lyrics.csv"
DEFAULT_OUT = PROJECT_ROOT / "R_data" / "corpus" / "eval" / "queries.jsonl"

MOOD_QUERIES = [
    ("maya lagcha", "romance"),
    ("prem", "romance"),
    ("dukha", "sadness"),
    ("sad song", "sadness"),
    ("desh bhakti", "patriotic"),
    ("nepal", "patriotic"),
    ("khusi", "joy"),
    ("party song", "party"),
    ("jindagi", "life"),
    ("sapana", "dream"),
    ("माया", "romance-dev"),
    ("दुख", "sadness-dev"),
    ("देश", "patriotic-dev"),
    ("आमा", "family"),
    ("साथी", "friendship"),
]


def text_for_query(line: str, words: int = 8) -> str:
    tokens = line.split()
    if len(tokens) <= words:
        return line
    return " ".join(tokens[:words])


def build_queries(
    cleaned_csv: Path,
    out_path: Path,
    *,
    n_artist: int = 40,
    n_lyric: int = 40,
    n_seed: int = 30,
    min_songs: int = 3,
    seed: int = 42,
) -> dict:
    rng = random.Random(seed)
    df = pd.read_csv(cleaned_csv, encoding="utf-8").fillna({"artist": "", "title": "", "lyrics": ""})
    queries: list[dict] = []

    artist_counts = df["artist"].value_counts()
    eligible = [a for a, n in artist_counts.items() if n >= min_songs and str(a).strip()]
    artist_pool = rng.sample(eligible, min(n_artist, len(eligible)))
    for index, artist in enumerate(artist_pool):
        ids = df.loc[df["artist"] == artist, "song_id"].astype(int).tolist()
        queries.append(
            {
                "query_id": f"artist_{index:03d}",
                "type": "artist",
                "text": str(artist),
                "relevant": ids,
                "meta": {"artist": str(artist), "n_songs": len(ids)},
            }
        )

    lyric_rows = df[df["lyrics"].str.len() >= 300]
    lyric_pool = lyric_rows.sample(min(n_lyric, len(lyric_rows)), random_state=seed)
    for index, row in enumerate(lyric_pool.itertuples(index=False)):
        lines = [line.strip() for line in str(row.lyrics).splitlines() if len(line.split()) >= 4]
        if not lines:
            continue
        line = rng.choice(lines)
        queries.append(
            {
                "query_id": f"lyric_{index:03d}",
                "type": "lyric",
                "text": text_for_query(line),
                "relevant": [int(row.song_id)],
                "meta": {"title": str(row.title), "artist": str(row.artist)},
            }
        )

    seed_pool = df.sample(min(n_seed, len(df)), random_state=seed + 1)
    for index, row in enumerate(seed_pool.itertuples(index=False)):
        same_artist = df.loc[df["artist"] == row.artist, "song_id"].astype(int).tolist()
        same_artist = [sid for sid in same_artist if sid != int(row.song_id)]
        queries.append(
            {
                "query_id": f"seed_{index:03d}",
                "type": "seed",
                "song_id": int(row.song_id),
                "relevant": same_artist,
                "meta": {"title": str(row.title), "artist": str(row.artist)},
            }
        )

    for index, (text, theme) in enumerate(MOOD_QUERIES):
        queries.append(
            {
                "query_id": f"mood_{index:03d}",
                "type": "mood",
                "text": text,
                "relevant": [],
                "meta": {"theme": theme, "judged": False},
            }
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        for query in queries:
            fh.write(json.dumps(query, ensure_ascii=False) + "\n")

    counts: dict[str, int] = {}
    for query in queries:
        counts[query["type"]] = counts.get(query["type"], 0) + 1
    return {"queries": len(queries), "by_type": counts, "output": str(out_path)}


def load_queries(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the evaluation query set.")
    parser.add_argument("--cleaned", type=Path, default=DEFAULT_CLEANED)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--n-artist", type=int, default=40)
    parser.add_argument("--n-lyric", type=int, default=40)
    parser.add_argument("--n-seed", type=int, default=30)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_queries(args.cleaned, args.out, n_artist=args.n_artist, n_lyric=args.n_lyric, n_seed=args.n_seed)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
