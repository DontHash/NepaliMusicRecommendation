"""Ranking metrics: nDCG@k, Recall@k, MRR."""

from __future__ import annotations

import math


def dcg(relevances: list[float], k: int) -> float:
    return sum(rel / math.log2(idx + 2) for idx, rel in enumerate(relevances[:k]))


def ndcg_at_k(ranked_relevances: list[float], k: int) -> float:
    ideal = sorted(ranked_relevances, reverse=True)
    ideal_score = dcg(ideal, k)
    if ideal_score == 0:
        return 0.0
    return dcg(ranked_relevances, k) / ideal_score


def recall_at_k(relevant: set[int], ranked_ids: list[int], k: int) -> float:
    if not relevant:
        return 0.0
    top = set(ranked_ids[:k])
    return len(relevant & top) / len(relevant)


def mrr(relevant: set[int], ranked_ids: list[int]) -> float:
    for idx, sid in enumerate(ranked_ids, start=1):
        if sid in relevant:
            return 1.0 / idx
    return 0.0


def evaluate_rankings(
    queries: list[dict],
    rankings: dict[str, list[int]],
    k_values: tuple[int, ...] = (10, 50),
) -> dict:
    per_query = []
    for query in queries:
        qid = query["query_id"]
        relevant = set(int(x) for x in query.get("relevant", []))
        ranked = [int(x) for x in rankings.get(qid, [])]
        entry = {"query_id": qid, "type": query["type"], "relevant": len(relevant)}
        rel_flags = [1.0 if sid in relevant else 0.0 for sid in ranked]
        for k in k_values:
            entry[f"ndcg@{k}"] = round(ndcg_at_k(rel_flags, k), 4)
            entry[f"recall@{k}"] = round(recall_at_k(relevant, ranked, k), 4)
        entry["mrr"] = round(mrr(relevant, ranked), 4)
        per_query.append(entry)

    summary: dict[str, dict] = {}
    by_type: dict[str, list[dict]] = {}
    for entry in per_query:
        by_type.setdefault(entry["type"], []).append(entry)
    for qtype, entries in by_type.items():
        agg = {}
        keys = [key for key in entries[0] if key not in {"query_id", "type", "relevant"}]
        for key in keys:
            agg[key] = round(sum(e[key] for e in entries) / len(entries), 4)
        agg["queries"] = len(entries)
        summary[qtype] = agg
    return {"summary": summary, "per_query": per_query}
