"""Run the retrieval evaluation against the current recommender artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.metrics import evaluate_rankings  # noqa: E402
from eval.queries import DEFAULT_OUT, load_queries  # noqa: E402
from music_rec.config import Config  # noqa: E402

DEFAULT_REPORT = PROJECT_ROOT / "music_rec_artifacts" / "eval_v2_report.json"


def run_eval(queries_path: Path, report_path: Path, *, ann_top_k: int = 200, top_k: int = 50) -> dict:
    from music_rec.recommender import MusicRecommender

    config = Config()
    config.ann_top_k = ann_top_k
    config.final_top_k = top_k
    recommender = MusicRecommender.load(config)

    queries = load_queries(queries_path)
    rankings: dict[str, list[int]] = {}
    for query in queries:
        qtype = query["type"]
        if qtype in {"mood"}:
            continue
        if qtype == "seed":
            results = recommender.recommend_by_song(int(query["song_id"]))
        else:
            results = recommender.recommend_by_text(str(query["text"]))
        ids = [rec.song_id for rec in results]
        if qtype == "lyric":
            source = set(int(x) for x in query["relevant"])
            ids = [sid for sid in ids if sid not in source]
        rankings[query["query_id"]] = ids

    objective = [query for query in queries if query["type"] in {"artist", "lyric", "seed"}]
    report = evaluate_rankings(objective, rankings)
    report["meta"] = {
        "queries_path": str(queries_path),
        "corpus_size": int(len(recommender.songs)),
        "ann_top_k": ann_top_k,
        "top_k": top_k,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality.")
    parser.add_argument("--queries", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--ann-top-k", type=int, default=200)
    parser.add_argument("--top-k", type=int, default=50)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.queries.exists():
        raise SystemExit(f"missing queries file: {args.queries}; run eval/queries.py first")
    report = run_eval(args.queries, args.report, ann_top_k=args.ann_top_k, top_k=args.top_k)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"report -> {args.report}")


if __name__ == "__main__":
    main()
