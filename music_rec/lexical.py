"""BM25 lexical index over lyric text, fused with dense retrieval scores.

Dense embeddings are weak at verbatim line recall on Nepali lyrics; a lexical
index built from the same cleaned corpus recovers near-exact queries. The two
signals are combined per song before reranking.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Sequence

import numpy as np
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import CountVectorizer

from .tokenization import tokenize
from .typo_map import TypoMap

DEFAULT_K1 = 1.5
DEFAULT_B = 0.75
DEFAULT_PHRASE_CANDIDATES = 2000
DEFAULT_MIN_TOKENS = 3
DEFAULT_SHORT_IDF = 2.5
DEFAULT_FUZZY_MAX_DF = 10
DEFAULT_FUZZY_THRESHOLD = 70.0
DEFAULT_FUZZY_WEIGHT = 0.8
DEFAULT_FUZZY_MAX_CANDIDATES = 3
DEFAULT_FUZZY_MIN_LENGTH = 3
_FUZZY_NGRAM_SIZES = (2, 3)
_FUZZY_POOL = 200

_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def _skeleton(token: str) -> str:
    """Drop combining marks (matras) so vowel-only spelling differences match."""
    text = unicodedata.normalize("NFC", token)
    return "".join(
        ch
        for ch in text
        if not unicodedata.category(ch).startswith("M") and ch not in "\u200c\u200d"
    )


class LexicalIndex:
    def __init__(
        self,
        lyrics: Sequence[str],
        *,
        k1: float = DEFAULT_K1,
        b: float = DEFAULT_B,
        min_df: int = 1,
        phrase_candidates: int = DEFAULT_PHRASE_CANDIDATES,
        fuzzy_enabled: bool = True,
        fuzzy_max_df: int = DEFAULT_FUZZY_MAX_DF,
        fuzzy_threshold: float = DEFAULT_FUZZY_THRESHOLD,
        fuzzy_weight: float = DEFAULT_FUZZY_WEIGHT,
        fuzzy_max_candidates: int = DEFAULT_FUZZY_MAX_CANDIDATES,
        typo_map: TypoMap | None = None,
    ):
        self.k1 = float(k1)
        self.b = float(b)
        self.phrase_candidates = int(phrase_candidates)
        self.fuzzy_enabled = bool(fuzzy_enabled)
        self.fuzzy_max_df = int(fuzzy_max_df)
        self.fuzzy_threshold = float(fuzzy_threshold)
        self.fuzzy_weight = float(fuzzy_weight)
        self.fuzzy_max_candidates = int(fuzzy_max_candidates)
        self.typo_map = typo_map or TypoMap()
        texts = [str(text or "") for text in lyrics]
        raw_docs = [tokenize(text) for text in texts]
        raw_counts = Counter(token for doc in raw_docs for token in set(doc))
        docs = [self._map_doc(doc, raw_counts) for doc in raw_docs]
        self.n_songs = len(docs)
        self._vectorizer = CountVectorizer(analyzer=lambda tokens: tokens, min_df=min_df, dtype=np.float32)
        matrix = self._vectorizer.fit_transform(docs) if docs else None
        self._matrix = matrix.tocsr() if matrix is not None else None
        if self._matrix is None:
            self._idf = np.zeros(0, dtype=np.float32)
            self._doc_len = np.zeros(0, dtype=np.float32)
            self._df_counts = np.zeros(0, dtype=np.int32)
            self.avgdl = 0.0
            self._doc_token_ids: list[np.ndarray] = []
        else:
            self._doc_len = np.asarray(self._matrix.sum(axis=1)).ravel().astype(np.float32)
            self.avgdl = float(self._doc_len.mean())
            self._df_counts = np.asarray((self._matrix > 0).sum(axis=0)).ravel().astype(np.int32)
            self._idf = np.log(
                (self.n_songs - self._df_counts + 0.5) / (self._df_counts + 0.5) + 1.0
            ).astype(np.float32)
            vocab = self._vectorizer.vocabulary_
            self._doc_token_ids = [
                np.asarray([vocab[token] for token in doc if token in vocab], dtype=np.int32)
                for doc in docs
            ]
        self._csc = None
        self._tokens_by_id = self._build_tokens_by_id()
        self._fuzzy_ngrams = self._build_fuzzy_ngrams()

    def _map_doc(self, doc: list[str], raw_counts: Counter) -> list[str]:
        """Apply reviewed typo mappings to a corpus document.

        Phrase entries always apply (they are long and specific); token entries
        only apply to tokens that are rare in the raw corpus, so the map can
        never rewrite common vocabulary.
        """
        if not self.typo_map.enabled:
            return doc
        mapped = self.typo_map.apply_phrases(doc)
        return [
            self.typo_map.tokens.get(token, token)
            if raw_counts.get(token, 0) <= self.fuzzy_max_df
            else token
            for token in mapped
        ]

    def _query_tokens(self, query: str) -> list[str]:
        """Tokenize a query and apply typo mappings under the same rarity rule."""
        tokens = tokenize(query or "")
        if not self.typo_map.enabled:
            return tokens
        mapped = self.typo_map.apply_phrases(tokens)
        vocab = self._vectorizer.vocabulary_
        result = []
        for token in mapped:
            column = vocab.get(token)
            if token in self.typo_map.tokens and (
                column is None or self._df_counts[column] <= self.fuzzy_max_df
            ):
                token = self.typo_map.tokens[token]
            result.append(token)
        return result

    def _build_tokens_by_id(self) -> list[str]:
        if self._matrix is None:
            return []
        tokens = [""] * len(self._vectorizer.vocabulary_)
        for token, column in self._vectorizer.vocabulary_.items():
            tokens[column] = token
        return tokens

    def _build_fuzzy_ngrams(self) -> dict[str, list[int]]:
        if not self.fuzzy_enabled:
            return {}
        index: dict[str, list[int]] = {}
        for token_id, token in enumerate(self._tokens_by_id):
            for size in _FUZZY_NGRAM_SIZES:
                for start in range(len(token) - size + 1):
                    index.setdefault(token[start : start + size], []).append(token_id)
        return index

    def _fuzzy_expansions(self, token: str) -> list[tuple[int, float]]:
        """Near-neighbour vocabulary tokens for an unseen or rare query token.

        Only tokens that are OOV or rare are expanded, and rare query tokens
        only expand to rare candidates: common tokens are exact-matched and
        expanding them would dilute ranking with broad low-idf boosts.
        """
        if not self.fuzzy_enabled or len(token) < DEFAULT_FUZZY_MIN_LENGTH:
            return []
        shared: Counter[int] = Counter()
        for size in _FUZZY_NGRAM_SIZES:
            for start in range(len(token) - size + 1):
                for token_id in self._fuzzy_ngrams.get(token[start : start + size], ()):
                    shared[token_id] += 1
        if not shared:
            return []
        pool = sorted(shared.items(), key=lambda item: -item[1])[:_FUZZY_POOL]
        scored: list[tuple[int, float]] = []
        for token_id, _ in pool:
            candidate = self._tokens_by_id[token_id]
            if candidate == token:
                continue
            ratio = max(
                float(fuzz.ratio(token, candidate)),
                float(fuzz.ratio(_skeleton(token), _skeleton(candidate))),
            )
            if ratio >= self.fuzzy_threshold:
                scored.append((token_id, ratio / 100.0 * self.fuzzy_weight))
        scored.sort(key=lambda item: -item[1])
        return scored[: self.fuzzy_max_candidates]

    def _postings(self):
        if self._csc is None:
            self._csc = self._matrix.tocsc()
        return self._csc

    def should_fuse(
        self,
        query: str,
        *,
        min_tokens: int = DEFAULT_MIN_TOKENS,
        short_idf: float = DEFAULT_SHORT_IDF,
    ) -> bool:
        """Whether a query is specific enough for lexical fusion.

        Short keyword queries (mood searches like ``dukha`` or ``maya lagcha``)
        stay dense-only: matching the literal word finds songs that mention it,
        not songs that feel it. A two-token query fuses only when both tokens
        are rare and Devanagari, i.e. a romanized lyric fragment rather than a
        short English keyword pair such as ``sad song``.
        """
        if self._matrix is None:
            return False
        vocab = self._vectorizer.vocabulary_
        tokens = [token for token in self._query_tokens(query) if token in vocab]
        if len(tokens) < 2:
            return False
        if len(tokens) >= min_tokens:
            return True
        if not any(_DEVANAGARI_RE.search(token) for token in tokens):
            return False
        return float(min(self._idf[vocab[token]] for token in tokens)) >= short_idf

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
        tokens = self._query_tokens(query)
        query_ids = [vocab[token] for token in tokens if token in vocab]
        weights: Counter[int] = Counter(query_ids)
        if self.fuzzy_enabled:
            for token in tokens:
                column = vocab.get(token)
                if column is not None and self._df_counts[column] > self.fuzzy_max_df:
                    continue
                for candidate, weight in self._fuzzy_expansions(token):
                    if candidate == column:
                        continue
                    if (
                        column is not None
                        and self._df_counts[candidate] > self.fuzzy_max_df
                    ):
                        continue
                    weights[candidate] += weight
        if not weights:
            return scores
        postings = self._postings()
        for column_index, query_freq in weights.items():
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
