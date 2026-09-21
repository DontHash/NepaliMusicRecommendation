"""Mood / free-text retrieval evaluation.

The objective lyric/artist/seed eval (``eval/run_eval.py``) skips mood queries
because they have no per-song relevance judgments. This harness scores them
with two judgment layers:

- **Weak labels** (``R_data/raw/gemini/corpus_v3/labels_merged.csv``, 4k songs):
  precision@10 of retrieving songs whose Gemini-labeled emotion matches the
  query theme. Full coverage, LLM-generated.
- **Human gold** (``eval/mood_gold.csv``, 147 reviewed songs): hit@10, i.e. at
  least one top-10 song carries the target emotion in the hand labels. Small
  but human.

Both the hybrid (lexical + dense) and the dense-only rankings are scored so a
fusion regression is visible per query instead of hidden in an average.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from music_rec.config import Config  # noqa: E402

DEFAULT_QUERIES = PROJECT_ROOT / "R_data" / "corpus" / "eval" / "queries.jsonl"
DEFAULT_WEAK_LABELS = (
    PROJECT_ROOT / "R_data" / "raw" / "gemini" / "corpus_v3" / "labels_merged.csv"
)
DEFAULT_GOLD = PROJECT_ROOT / "eval" / "mood_gold.csv"
DEFAULT_REPORT = PROJECT_ROOT / "music_rec_artifacts" / "eval_mood_retrieval_report.json"

THEME_TO_LABEL: dict[str, str | None] = {
    "romance": "positive",
    "romance-dev": "positive",
    "patriotic": "positive",
    "family": "positive",
    "friendship": "positive",
    "sadness": "sadness",
    "joy": "joy",
    "party": "joy",
    "life": None,
    "dream": None,
}


def map_theme(theme: str) -> str | None:
    return THEME_TO_LABEL.get(theme)


def precision_at_k(ranked: list[int], relevant: set[int], k: int = 10) -> float:
    top = list(ranked)[:k]
    if not top:
        return 0.0
    return len([song_id for song_id in top if song_id in relevant]) / len(top)


def hit_at_k(ranked: list[int], relevant: set[int], k: int = 10) -> float:
    return 1.0 if any(song_id in relevant for song_id in list(ranked)[:k]) else 0.0


def _label_sets(frame: pd.DataFrame, labels: tuple[str, ...]) -> dict[str, set[int]]:
    sets: dict[str, set[int]] = {}
    for label in labels:
        if label in frame.columns:
            sets[label] = set(frame.loc[frame[label] == 1, "song_id"].astype(int))
    return sets


def load_weak_sets(frame: pd.DataFrame) -> dict[str, set[int]]:
    return _label_sets(frame, ("joy", "sadness", "anger", "positive"))


def load_gold_sets(frame: pd.DataFrame) -> dict[str, set[int]]:
    return _label_sets(frame, ("joy", "sadness", "anger"))


def load_queries(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def rank_queries(recommender, queries: list[dict]) -> dict[str, list[int]]:
    rankings: dict[str, list[int]] = {}
    for query in queries:
        results = recommender.recommend_by_text(str(query["text"]))
        rankings[query["query_id"]] = [int(rec.song_id) for rec in results]
    return rankings


def _gold_base_rate(gold: set[int], corpus_size: int, k: int) -> float:
    if corpus_size <= 0:
        return 0.0
    return 1.0 - (1.0 - len(gold) / corpus_size) ** k


def evaluate(
    queries: list[dict],
    rankings: dict[str, list[int]],
    weak_sets: dict[str, set[int]],
    gold_sets: dict[str, set[int]],
    corpus_size: int,
    *,
    k: int = 10,
) -> dict:
    per_query = []
    for query in queries:
        theme = str(query.get("meta", {}).get("theme", ""))
        label = map_theme(theme)
        entry = {
            "query_id": query["query_id"],
            "text": query["text"],
            "theme": theme,
            "label": label,
        }
        if label is not None:
            weak = weak_sets.get(label, set())
            gold = gold_sets.get(label, set())
            ranked = rankings.get(query["query_id"], [])
            entry[f"precision@{k}"] = round(precision_at_k(ranked, weak, k), 4)
            entry["weak_base_rate"] = round(len(weak) / corpus_size, 4)
            entry[f"gold_hit@{k}"] = hit_at_k(ranked, gold, k)
            entry["gold_base_rate"] = round(_gold_base_rate(gold, corpus_size, k), 4)
        per_query.append(entry)

    mapped = [entry for entry in per_query if entry["label"] is not None]
    by_label: dict[str, dict] = {}
    for label in sorted({entry["label"] for entry in mapped}):
        rows = [entry for entry in mapped if entry["label"] == label]
        by_label[label] = {
            "queries": len(rows),
            f"precision@{k}": round(
                sum(row[f"precision@{k}"] for row in rows) / len(rows), 4
            ),
            "weak_base_rate": rows[0]["weak_base_rate"],
            f"gold_hit@{k}": round(sum(row[f"gold_hit@{k}"] for row in rows) / len(rows), 4),
            "gold_base_rate": rows[0]["gold_base_rate"],
        }

    summary = {
        "queries": len(per_query),
        "mapped": len(mapped),
        f"precision@{k}": round(
            sum(entry[f"precision@{k}"] for entry in mapped) / len(mapped), 4
        )
        if mapped
        else None,
        f"gold_hit@{k}": round(
            sum(entry[f"gold_hit@{k}"] for entry in mapped) / len(mapped), 4
        )
        if mapped
        else None,
    }
    return {"summary": summary, "by_label": by_label, "per_query": per_query}


def run(
    queries_path: Path = DEFAULT_QUERIES,
    weak_path: Path = DEFAULT_WEAK_LABELS,
    gold_path: Path = DEFAULT_GOLD,
    report_path: Path = DEFAULT_REPORT,
    *,
    top_k: int = 10,
) -> dict:
    from music_rec.recommender import MusicRecommender

    for path in (queries_path, weak_path, gold_path):
        if not path.exists():
            raise SystemExit(f"missing input: {path}")

    queries = [query for query in load_queries(queries_path) if query["type"] == "mood"]
    weak_sets = load_weak_sets(pd.read_csv(weak_path, encoding="utf-8"))
    gold_sets = load_gold_sets(pd.read_csv(gold_path, encoding="utf-8"))
    corpus_size = len(pd.read_csv(Config().cleaned_lyrics_csv, encoding="utf-8"))

    config = Config()
    config.final_top_k = top_k
    recommender = MusicRecommender.load(config)
    hybrid_rankings = rank_queries(recommender, queries)
    config.lexical_enabled = False
    config.dedup_enabled = False
    dense_rankings = rank_queries(recommender, queries)

    report = {
        "hybrid": evaluate(queries, hybrid_rankings, weak_sets, gold_sets, corpus_size, k=top_k),
        "dense_only": evaluate(queries, dense_rankings, weak_sets, gold_sets, corpus_size, k=top_k),
        "meta": {
            "queries_path": str(queries_path),
            "weak_labels_path": str(weak_path),
            "gold_path": str(gold_path),
            "corpus_size": corpus_size,
            "top_k": top_k,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate mood/free-text retrieval.")
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERIES)
    parser.add_argument("--weak-labels", type=Path, default=DEFAULT_WEAK_LABELS)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--top-k", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run(
        args.queries,
        args.weak_labels,
        args.gold,
        args.report,
        top_k=args.top_k,
    )
    for name in ("hybrid", "dense_only"):
        print(f"{name}: {json.dumps(report[name]['summary'], ensure_ascii=False)}")
    print(f"report -> {args.report}")


if __name__ == "__main__":
    main()
