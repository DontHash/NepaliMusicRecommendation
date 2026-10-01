"""Offline check: does audio similarity improve seed recommendations?

Fair comparison restricted to songs that actually have audio. Relevance uses
the same same-artist proxy as eval/queries.py seed queries.

Modes: text_only (corpus embeddings), audio_only (CLAP), fused@w for several
weights. Reports paired bootstrap 95% CIs for fused@w minus text_only, so the
result is not a point estimate on a small sample.

  python scripts/audio/eval_audio_seed.py --all-covered
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audio import config as audio_config, utils  # noqa: E402
from eval.metrics import ndcg_at_k, recall_at_k  # noqa: E402
from eval.queries import DEFAULT_OUT, load_queries  # noqa: E402
from music_rec.config import Config  # noqa: E402

WEIGHTS = (0.3, 0.5, 0.7)


def rank_ids(scores, ids):
    order = sorted(range(len(ids)), key=lambda i: -scores[i])
    return [ids[i] for i in order]


def paired_bootstrap(diffs, *, iterations: int = 2000, seed: int = 7) -> dict:
    import numpy as np

    values = np.asarray(diffs, dtype=np.float64)
    rng = np.random.default_rng(seed)
    means = [float(rng.choice(values, size=len(values), replace=True).mean()) for _ in range(iterations)]
    low, high = float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))
    return {
        "mean_delta": round(float(values.mean()), 4),
        "ci95_low": round(low, 4),
        "ci95_high": round(high, 4),
        "p_delta_positive": round(float((values > 0).mean()), 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=PROJECT_ROOT / "R_data" / "audio" / "eval_audio_seed_report.json")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--all-covered", action="store_true",
                        help="generate seed queries from every audio-covered song with same-artist siblings")
    args = parser.parse_args()

    import numpy as np

    from music_rec.recommender import MusicRecommender

    config = Config()
    recommender = MusicRecommender.load(config)
    index = recommender.audio_index
    if index is None:
        raise SystemExit("audio index unavailable; run scripts/audio/embed_audio.py first")

    covered = list(index.song_ids)
    covered_rows = [recommender._row_index(sid) for sid in covered]
    embeddings = recommender.embeddings[np.asarray(covered_rows)]

    if args.all_covered:
        songs = recommender.songs
        by_artist: dict[str, list[int]] = {}
        for song_id in covered:
            by_artist.setdefault(str(songs.loc[song_id, "artist"]), []).append(int(song_id))
        queries = [
            {"query_id": f"covered_{sid}", "song_id": sid, "relevant": [s for s in siblings if s != sid]}
            for siblings in by_artist.values() if len(siblings) >= 2
            for sid in siblings
        ]
    else:
        if not args.queries.exists():
            raise SystemExit(f"missing queries file: {args.queries}; run eval/queries.py first")
        queries = [q for q in load_queries(args.queries) if q["type"] == "seed"]

    per_query: dict[str, list[float]] = {}
    per_query_recall: dict[str, list[float]] = {}
    skipped: list[int] = []
    for query in queries:
        target = int(query["song_id"])
        if not index.has_audio(target):
            skipped.append(target)
            continue
        relevant = {int(sid) for sid in query["relevant"]} & set(covered)
        relevant.discard(target)
        if not relevant:
            skipped.append(target)
            continue
        text_scores = embeddings @ recommender.embeddings[recommender._row_index(target)]
        audio_ids, audio_scores = index.scores_for_song(target)
        audio_map = {int(sid): float(score) for sid, score in zip(audio_ids, audio_scores)}

        def score_ranking(weights_row):
            ranking = [sid for sid in rank_ids(list(weights_row), covered) if sid != target][: args.top_k]
            flags = [1.0 if sid in relevant else 0.0 for sid in ranking]
            return ndcg_at_k(flags, args.top_k), recall_at_k(relevant, ranking, args.top_k)

        text_ndcg, text_recall = score_ranking(text_scores)
        per_query.setdefault("text_only", []).append(text_ndcg)
        per_query_recall.setdefault("text_only", []).append(text_recall)

        audio_ranking = [sid for sid in rank_ids(list(audio_scores), list(audio_ids)) if sid != target][: args.top_k]
        audio_flags = [1.0 if sid in relevant else 0.0 for sid in audio_ranking]
        per_query.setdefault("audio_only", []).append(ndcg_at_k(audio_flags, args.top_k))
        per_query_recall.setdefault("audio_only", []).append(recall_at_k(relevant, audio_ranking, args.top_k))

        for weight in WEIGHTS:
            fused = np.array([
                (1.0 - weight) * float(text_scores[row]) + weight * audio_map.get(sid, 0.0)
                for row, sid in enumerate(covered)
            ])
            fused_ndcg, fused_recall = score_ranking(fused)
            per_query.setdefault(f"fused@{weight}", []).append(fused_ndcg)
            per_query_recall.setdefault(f"fused@{weight}", []).append(fused_recall)

    modes = ["text_only", "audio_only"] + [f"fused@{w}" for w in WEIGHTS]
    summary = {
        mode: {
            "queries": len(per_query.get(mode, [])),
            f"nDCG@{args.top_k}": round(float(np.mean(per_query[mode])), 4),
            f"Recall@{args.top_k}": round(float(np.mean(per_query_recall[mode])), 4),
        }
        for mode in modes
        if per_query.get(mode)
    }
    significance = {
        mode: paired_bootstrap([
            fused - text
            for fused, text in zip(per_query[mode], per_query["text_only"])
        ])
        for mode in modes if mode.startswith("fused@")
    }
    best_mode = max((m for m in modes if m.startswith("fused@")), key=lambda m: np.mean(per_query[m]))

    report = {
        "schema_version": audio_config.SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": utils.git_sha(),
        "seed_queries": len(queries),
        "evaluated": len(per_query.get("text_only", [])),
        "skipped_no_audio_or_gold": skipped,
        "audio_covered_songs": len(covered),
        "weights": list(WEIGHTS),
        "summary": summary,
        "paired_bootstrap_fused_minus_text": significance,
        "best_fused_mode": best_mode,
        "note": "restricted to audio-covered songs so audio-only modes are not structurally capped; relevance is the same-artist proxy",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"skipped_no_audio_or_gold"}}, indent=2))
    print(f"report -> {args.report}")


if __name__ == "__main__":
    main()
