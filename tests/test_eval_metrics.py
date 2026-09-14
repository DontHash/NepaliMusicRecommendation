"""Unit tests for ranking metrics."""

from __future__ import annotations

from eval.metrics import evaluate_rankings, mrr, ndcg_at_k, recall_at_k


def test_ndcg_perfect_ranking():
    assert ndcg_at_k([1.0, 1.0, 0.0], 3) == 1.0


def test_ndcg_reversed_ranking_is_lower():
    perfect = ndcg_at_k([1.0, 1.0, 0.0, 0.0], 4)
    reversed_score = ndcg_at_k([0.0, 0.0, 1.0, 1.0], 4)
    assert perfect == 1.0
    assert reversed_score < perfect


def test_ndcg_no_relevant():
    assert ndcg_at_k([0.0, 0.0], 2) == 0.0


def test_recall_at_k():
    relevant = {1, 2, 3}
    ranked = [9, 1, 5, 2]
    assert recall_at_k(relevant, ranked, 2) == 1 / 3
    assert recall_at_k(relevant, ranked, 4) == 2 / 3
    assert recall_at_k(set(), ranked, 4) == 0.0


def test_mrr():
    assert mrr({5}, [1, 2, 5]) == 1 / 3
    assert mrr({5}, [5, 2]) == 1.0
    assert mrr({5}, [1, 2]) == 0.0


def test_evaluate_rankings_aggregates_by_type():
    queries = [
        {"query_id": "a_0", "type": "artist", "relevant": [1, 2]},
        {"query_id": "l_0", "type": "lyric", "relevant": [5]},
        {"query_id": "m_0", "type": "mood", "relevant": []},
    ]
    rankings = {"a_0": [1, 3, 2], "l_0": [4, 5, 6], "m_0": [7, 8]}
    report = evaluate_rankings(queries, rankings)
    assert report["summary"]["artist"]["queries"] == 1
    assert report["summary"]["lyric"]["recall@10"] == 1.0
    assert report["summary"]["mood"]["recall@10"] == 0.0
