"""BM25 lexical index over lyric text, fused with dense retrieval scores.

Dense embeddings are weak at verbatim line recall on Nepali lyrics; a lexical
index built from the same cleaned corpus recovers near-exact queries. The two
signals are combined per song before reranking.
"""

from __future__ import annotations

from collections import Counter
from typing import Sequence

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer

from .tokenization import tokenize

DEFAULT_K1 = 1.5
DEFAULT_B = 0.75
DEFAULT_PHRASE_CANDIDATES = 2000


class LexicalIndex:
    def __init__(
        self,
        lyrics: Sequence[str],
        *,
        k1: float = DEFAULT_K1,
        b: float = DEFAULT_B,
        min_df: int = 1,
        phrase_candidates: int = DEFAULT_PHRASE_CANDIDATES,
    ):
        self.k1 = float(k1)
        self.b = float(b)
        self.phrase_candidates = int(phrase_candidates)
        texts = [str(text or "") for text in lyrics]
        docs = [tokenize(text) for text in texts]
        self.n_songs = len(docs)
        self._vectorizer = CountVectorizer(analyzer=lambda tokens: tokens, min_df=min_df, dtype=np.float32)
        matrix = self._vectorizer.fit_transform(docs) if docs else None
        self._matrix = matrix.tocsr() if matrix is not None else None
        if self._matrix is None:
            self._idf = np.zeros(0, dtype=np.float32)
            self._doc_len = np.zeros(0, dtype=np.float32)
            self.avgdl = 0.0
            self._doc_token_ids: list[np.ndarray] = []
        else:
            self._doc_len = np.asarray(self._matrix.sum(axis=1)).ravel().astype(np.float32)
            self.avgdl = float(self._doc_len.mean())
            df_counts = np.asarray((self._matrix > 0).sum(axis=0)).ravel()
            self._idf = np.log(
                (self.n_songs - df_counts + 0.5) / (df_counts + 0.5) + 1.0
            ).astype(np.float32)
            vocab = self._vectorizer.vocabulary_
            self._doc_token_ids = [
                np.asarray([vocab[token] for token in doc if token in vocab], dtype=np.int32)
                for doc in docs
            ]
        self._csc = None

    def _postings(self):
        if self._csc is None:
            self._csc = self._matrix.tocsc()
        return self._csc

    def _phrase_rows(self, query_ids: np.ndarray, candidates: np.ndarray) -> np.ndarray:
        size = len(query_ids)
        matches = []
        for row in candidates:
            sequence = self._doc_token_ids[row]
            if sequence.size < size:
                continue
            for start in np.flatnonzero(sequence == query_ids[0]):
                if start + size <= sequence.size and np.array_equal(
                    sequence[start : start + size], query_ids
                ):
                    matches.append(row)
                    break
        return np.asarray(matches, dtype=np.int64)

    def song_scores(self, query: str) -> np.ndarray:
        scores = np.zeros(self.n_songs, dtype=np.float32)
        if self._matrix is None:
            return scores
        vocab = self._vectorizer.vocabulary_
        query_ids = [vocab[token] for token in tokenize(query or "") if token in vocab]
        if not query_ids:
            return scores
        postings = self._postings()
        for column_index, query_freq in Counter(query_ids).items():
            column = postings[:, column_index]
            rows = column.indices
            if rows.size == 0:
                continue
            term_freq = column.data.astype(np.float32)
            length_norm = 1.0 - self.b + self.b * self._doc_len[rows] / self.avgdl
            denominator = term_freq + self.k1 * length_norm
            scores[rows] += (
                (self._idf[column_index] * query_freq)
                * (term_freq * (self.k1 + 1.0) / denominator)
            )
        if len(query_ids) > 1 and self._doc_token_ids:
            limit = min(self.phrase_candidates, self.n_songs)
            candidates = np.argsort(-scores, kind="stable")[:limit]
            phrase_rows = self._phrase_rows(np.asarray(query_ids, dtype=np.int32), candidates)
            if phrase_rows.size:
                bonus = float(sum(self._idf[index] for index in set(query_ids)))
                scores[phrase_rows] += bonus
        return scores


def normalize_scores(scores: np.ndarray) -> np.ndarray:
    values = np.nan_to_num(np.asarray(scores, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)
    low, high = values.min(), values.max()
    if high <= low:
        return np.zeros_like(values)
    return (values - low) / (high - low)


def fuse_scores(
    dense_scores: np.ndarray, lexical_scores: np.ndarray, lexical_weight: float
) -> np.ndarray:
    if not 0.0 <= lexical_weight <= 1.0:
        raise ValueError(f"lexical_weight must be in [0, 1], got {lexical_weight}")
    fused = (1.0 - lexical_weight) * normalize_scores(dense_scores) + lexical_weight * normalize_scores(
        lexical_scores
    )
    return fused.astype(np.float32)
