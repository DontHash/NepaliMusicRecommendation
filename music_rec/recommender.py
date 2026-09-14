"""Recommend songs by text or seed song_id (ANN + MMR rerank)."""

from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import Config
from .index import build_index, load_index, normalize, search
from .query import QueryEncoder
from .rerank import mmr_rerank, sentiment_alignment


@dataclass
class Recommendation:
    song_id: int
    title: str
    artist: str
    score: float
    sentiment_score: float | None = None


class MusicRecommender:
    def __init__(self, config: Config | None = None, use_features: bool = True):
        self.config = config or Config()
        self.use_features = use_features
        self.songs = pd.read_csv(self.config.cleaned_lyrics_csv, encoding="utf-8")
        self.songs = self.songs.set_index("song_id", drop=False)

        self.embeddings = normalize(np.load(self.config.embeddings_npy))

        if use_features and self.config.feature_matrix_npy.exists():
            self.index_vectors = np.load(self.config.feature_matrix_npy).astype(np.float32)
        else:
            self.index_vectors = self.embeddings.copy()

        if self.config.faiss_index_path.exists():
            self.index = load_index(self.config.faiss_index_path)
        else:
            self.index = build_index(self.index_vectors.copy(), self.config.faiss_index_path)

        self.sentiment = None
        if self.config.sentiment_scores_csv.exists():
            self.sentiment = pd.read_csv(self.config.sentiment_scores_csv).set_index("song_id")

        self._query_encoder = None

    @classmethod
    def load(cls, config: Config | None = None, use_features: bool = True) -> "MusicRecommender":
        return cls(config=config, use_features=use_features)

    @property
    def query_encoder(self) -> QueryEncoder:
        if self._query_encoder is None:
            self._query_encoder = QueryEncoder(self.config)
        return self._query_encoder

    def _sent_score(self, song_id: int):
        if self.sentiment is None or song_id not in self.sentiment.index:
            return None
        return float(self.sentiment.loc[song_id, "sentiment_score"])

    def _row_index(self, song_id: int) -> int:
        return int(np.where(self.songs["song_id"].to_numpy() == song_id)[0][0])

    def _filter_mask(self, artist: str | None, category: str | None) -> np.ndarray:
        mask = np.ones(len(self.songs), dtype=bool)
        if artist:
            mask &= self.songs["artist"].fillna("").str.contains(artist, case=False).to_numpy()
        if category:
            mask &= (self.songs["category"].fillna("") == category).to_numpy()
        return mask

    def _rank(
        self,
        query_vec_index: np.ndarray,
        target_sentiment: float | None,
        exclude_id: int | None,
        artist: str | None,
        category: str | None,
    ) -> list[Recommendation]:
        cfg = self.config
        scores, ids = search(self.index, query_vec_index, min(cfg.ann_top_k * 3, len(self.songs)))

        keep_mask = self._filter_mask(artist, category)
        cand_ids, cand_rel = [], []
        for sid, sc in zip(ids, scores):
            if sid < 0 or sid == exclude_id:
                continue
            if not keep_mask[sid]:
                continue
            cand_ids.append(int(sid))
            cand_rel.append(float(sc))
            if len(cand_ids) >= cfg.ann_top_k:
                break

        if not cand_ids:
            return []

        cand_ids = np.array(cand_ids)
        relevance = np.array(cand_rel, dtype=np.float64)

        if self.sentiment is not None and target_sentiment is not None:
            cand_sent = np.array([self._sent_score(int(s)) or 0.0 for s in cand_ids])
            align = sentiment_alignment(cand_sent, target_sentiment)
            relevance = (1 - cfg.sentiment_weight) * relevance + cfg.sentiment_weight * align

        diversity_vecs = np.vstack([self.embeddings[self._row_index(int(s))] for s in cand_ids])
        ordered = mmr_rerank(cand_ids, relevance, diversity_vecs, cfg.final_top_k, cfg.mmr_lambda)

        rel_map = {int(s): r for s, r in zip(cand_ids, relevance)}
        recs = []
        for sid in ordered:
            row = self.songs.loc[sid]
            recs.append(
                Recommendation(
                    song_id=int(sid),
                    title=str(row["title"]),
                    artist=str(row["artist"]),
                    score=round(float(rel_map[sid]), 4),
                    sentiment_score=self._sent_score(sid),
                )
            )
        return recs

    def recommend_by_song(
        self, song_id: int, artist: str | None = None, category: str | None = None
    ) -> list[Recommendation]:
        row_idx = self._row_index(song_id)
        query_vec = self.index_vectors[row_idx]
        return self._rank(query_vec, self._sent_score(song_id), song_id, artist, category)

    def _maybe_artist_filter(self, text: str) -> str | None:
        query = text.strip().casefold()
        if not query:
            return None
        artists = self.songs["artist"].fillna("").str.casefold()
        matches = self.songs.loc[artists == query, "artist"]
        if len(matches) >= 2:
            return str(matches.iloc[0])
        return None

    def recommend_by_text(
        self,
        text: str,
        artist: str | None = None,
        category: str | None = None,
        target_sentiment: float | None = None,
    ) -> list[Recommendation]:
        emb = self.query_encoder.encode_text(text)
        norm = np.linalg.norm(emb)
        if norm:
            emb = emb / norm
        if artist is None:
            artist = self._maybe_artist_filter(text)
        if self.index_vectors.shape[1] != emb.shape[0]:
            padded = np.zeros(self.index_vectors.shape[1], dtype=np.float32)
            padded[: emb.shape[0]] = emb
            query_vec = padded
        else:
            query_vec = emb
        return self._rank(query_vec, target_sentiment, None, artist, category)

    def normalized_query(self, text: str) -> str:
        return self.query_encoder.normalize_query(text)
