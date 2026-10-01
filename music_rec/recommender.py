"""Recommend songs by text or seed song_id (ANN + MMR rerank)."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import Config
from .dedup import DuplicateCollapser
from .index import build_index, load_index, normalize, search
from .lexical import LexicalIndex, corpus_digest, fuse_scores
from .query import QueryEncoder
from .rerank import mmr_rerank, sentiment_alignment
from .typo_map import load_typo_map
from .window_search import WindowIndex


@dataclass
class Recommendation:
    song_id: int
    title: str
    artist: str
    score: float
    sentiment_score: float | None = None


class MusicRecommender:
    def __init__(
        self,
        config: Config | None = None,
        use_features: bool = True,
        query_encoder: QueryEncoder | None = None,
    ):
        self.config = config or Config()
        self.use_features = use_features
        self.songs = pd.read_csv(self.config.cleaned_lyrics_csv, encoding="utf-8")
        self.songs = self.songs.set_index("song_id", drop=False)
        self.song_ids = self.songs["song_id"].to_numpy()
        self.row_of_song = {int(sid): row for row, sid in enumerate(self.song_ids)}

        self.embeddings = normalize(np.load(self.config.embeddings_npy))

        if use_features and self.config.feature_matrix_npy.exists():
            self.index_vectors = np.load(self.config.feature_matrix_npy).astype(np.float32)
        else:
            self.index_vectors = self.embeddings.copy()

        if self.config.faiss_index_path.exists():
            self.index = load_index(self.config.faiss_index_path)
        else:
            self.index = build_index(self.index_vectors.copy(), self.config.faiss_index_path)

        self.window_index = None
        if (
            self.config.use_window_search
            and self.config.window_vectors_npy.exists()
            and self.config.window_owners_npy.exists()
        ):
            self.window_index = WindowIndex.load(
                self.config.window_vectors_npy,
                self.config.window_owners_npy,
                len(self.songs),
                index_path=self.config.window_index_path,
                ann_top_k=self.config.window_ann_top_k,
                ann_mode=self.config.window_ann,
                ann_threshold=self.config.window_ann_threshold,
            )

        self.sentiment = None
        if self.config.sentiment_scores_csv.exists():
            self.sentiment = pd.read_csv(self.config.sentiment_scores_csv).set_index("song_id")

        self.audio_index = None
        if self.config.audio_enabled:
            try:
                from .audio_index import AudioIndex

                self.audio_index = AudioIndex.load(self.config)
            except Exception as error:  # noqa: BLE001 - audio is an optional signal
                import logging

                logging.getLogger(__name__).warning("audio index unavailable: %s", error)
                self.audio_index = None

        self._query_encoder = query_encoder
        self._lexical = None
        self._lexical_lock = threading.Lock()
        self._dedup = None
        self._dedup_lock = threading.Lock()

    @classmethod
    def load(cls, config: Config | None = None, use_features: bool = True) -> "MusicRecommender":
        return cls(config=config, use_features=use_features)

    @property
    def query_encoder(self) -> QueryEncoder:
        if self._query_encoder is None:
            self._query_encoder = QueryEncoder(self.config)
        return self._query_encoder

    @property
    def lexical(self) -> LexicalIndex:
        if self._lexical is None:
            with self._lexical_lock:
                if self._lexical is None:
                    lyrics = self.songs["lyrics"].fillna("").astype(str).tolist()
                    cached = None
                    if self.config.lexical_cache_enabled:
                        cached = LexicalIndex.load(
                            self.config.lexical_cache_path,
                            digest=corpus_digest(lyrics),
                        )
                    if cached is not None:
                        self._lexical = cached
                    else:
                        typo_map = load_typo_map(
                            self.config.corpus_typo_map_csv,
                            enabled=self.config.corpus_typo_map_enabled,
                        )
                        self._lexical = LexicalIndex(
                            lyrics,
                            k1=self.config.bm25_k1,
                            b=self.config.bm25_b,
                            fuzzy_enabled=self.config.lexical_fuzzy_enabled,
                            fuzzy_max_df=self.config.lexical_fuzzy_max_df,
                            fuzzy_threshold=self.config.lexical_fuzzy_threshold,
                            fuzzy_weight=self.config.lexical_fuzzy_weight,
                            fuzzy_max_candidates=self.config.lexical_fuzzy_max_candidates,
                            typo_map=typo_map,
                        )
                        if self.config.lexical_cache_enabled:
                            try:
                                self._lexical.save(
                                    self.config.lexical_cache_path,
                                    digest=corpus_digest(lyrics),
                                )
                            except OSError:
                                pass
        return self._lexical

    @property
    def dedup(self) -> DuplicateCollapser:
        if self._dedup is None:
            with self._dedup_lock:
                if self._dedup is None:
                    self._dedup = DuplicateCollapser(self.songs)
        return self._dedup

    def _sent_score(self, song_id: int):
        if self.sentiment is None or song_id not in self.sentiment.index:
            return None
        return float(self.sentiment.loc[song_id, "sentiment_score"])

    def _row_index(self, song_id: int) -> int:
        try:
            return self.row_of_song[int(song_id)]
        except KeyError as exc:
            raise KeyError(f"song_id {song_id} is not in the corpus") from exc

    def _filter_mask(self, artist: str | None, category: str | None) -> np.ndarray:
        mask = np.ones(len(self.songs), dtype=bool)
        if artist:
            mask &= self.songs["artist"].fillna("").str.contains(artist, case=False, regex=False).to_numpy()
        if category:
            mask &= (self.songs["category"].fillna("") == category).to_numpy()
        return mask

    def _rank(
        self,
        query_vec_index: np.ndarray | None,
        target_sentiment: float | None,
        exclude_id: int | None,
        artist: str | None,
        category: str | None,
        base_scores: np.ndarray | None = None,
    ) -> list[Recommendation]:
        cfg = self.config
        keep_mask = self._filter_mask(artist, category)
        exclude_row = self.row_of_song.get(int(exclude_id)) if exclude_id is not None else None

        if artist or category:
            mask_rows = np.nonzero(keep_mask)[0]
            if exclude_row is not None:
                mask_rows = mask_rows[mask_rows != exclude_row]
            if len(mask_rows) == 0:
                return []
            if base_scores is not None:
                sims = base_scores[mask_rows]
            else:
                query_emb = query_vec_index[: self.embeddings.shape[1]]
                sims = self.embeddings[mask_rows] @ query_emb
            order = np.argsort(-sims)[: cfg.ann_top_k]
            cand_ids = self.song_ids[mask_rows[order]]
            cand_rel = sims[order].astype(np.float64)
        elif base_scores is not None:
            order = np.argsort(-base_scores)[: cfg.ann_top_k * 2]
            order = [
                row for row in order
                if np.isfinite(base_scores[row]) and keep_mask[row] and row != exclude_row
            ][: cfg.ann_top_k]
            cand_ids = self.song_ids[np.asarray(order, dtype=int)]
            cand_rel = base_scores[order].astype(np.float64)
        else:
            scores, rows = search(self.index, query_vec_index, min(cfg.ann_top_k * 3, len(self.songs)))
            cand_ids, cand_rel = [], []
            for row, sc in zip(rows, scores):
                if row < 0 or row == exclude_row:
                    continue
                if not keep_mask[row]:
                    continue
                cand_ids.append(int(self.song_ids[row]))
                cand_rel.append(float(sc))
                if len(cand_ids) >= cfg.ann_top_k:
                    break

        if len(cand_ids) == 0:
            return []

        cand_ids = np.array(cand_ids)
        relevance = np.array(cand_rel, dtype=np.float64)

        if self.sentiment is not None and target_sentiment is not None:
            cand_sent = np.array([self._sent_score(int(s)) or 0.0 for s in cand_ids])
            align = sentiment_alignment(cand_sent, target_sentiment)
            relevance = (1 - cfg.sentiment_weight) * relevance + cfg.sentiment_weight * align

        if cfg.dedup_enabled and len(cand_ids) > 1:
            keep = self.dedup.keep_mask(cand_ids)
            cand_ids = cand_ids[keep]
            relevance = relevance[keep]

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
        blended = self._audio_blended_scores(song_id, row_idx)
        if blended is None:
            return self._rank(query_vec, self._sent_score(song_id), song_id, artist, category)
        return self._rank(None, self._sent_score(song_id), song_id, artist, category, base_scores=blended)

    def _audio_blended_scores(self, song_id: int, row_idx: int) -> np.ndarray | None:
        """Text scores blended with audio similarity to the seed song (if any).

        Rows without audio keep their text score, so the fusion never penalises
        songs outside the audio collection.
        """
        if self.audio_index is None or self.config.audio_weight <= 0:
            return None
        audio_ids, audio_scores = self.audio_index.scores_for_song(song_id)
        if not len(audio_ids):
            return None
        text_scores = self.embeddings @ self.embeddings[row_idx]
        audio_map = {int(sid): float(score) for sid, score in zip(audio_ids, audio_scores)}
        return self.audio_index.blend_rows(
            text_scores, self.song_ids, audio_map, self.config.audio_weight
        )

    def has_audio(self, song_id: int) -> bool:
        return self.audio_index is not None and self.audio_index.has_audio(song_id)

    def recommend_by_audio(
        self,
        track: str,
        artist: str | None = None,
        category: str | None = None,
    ) -> list[Recommendation]:
        """Audio-only similarity: rank corpus songs that sound like ``track``.

        ``track`` is a track key from ``R_data/audio/audio_embedding_keys.csv``
        (``artist|title``, normalized).
        """
        if self.audio_index is None:
            raise RuntimeError("audio index unavailable; run scripts/audio/embed_audio.py")
        audio_ids, audio_scores = self.audio_index.scores_for_track(track)
        if not len(audio_ids):
            raise KeyError(f"no audio track for {track!r}")
        base = np.full(len(self.songs), -np.inf, dtype=np.float32)
        for song_id, score in zip(audio_ids, audio_scores):
            row = self.row_of_song.get(int(song_id))
            if row is not None:
                base[row] = float(score)
        exclude_id = self.audio_index.song_for_track(track)
        return self._rank(None, None, exclude_id, artist, category, base_scores=base)

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
        base_scores = self.window_index.song_scores(emb) if self.window_index is not None else None
        normalized = self.query_encoder.normalize_query(text)
        lexical_applies = self.config.lexical_enabled and artist is None and self.lexical.should_fuse(
            normalized,
            min_tokens=self.config.lexical_min_tokens,
            short_idf=self.config.lexical_short_idf,
        )
        if lexical_applies:
            lexical_scores = self.lexical.song_scores(normalized)
            if lexical_scores.max() > 0:
                dense_scores = base_scores
                if dense_scores is None:
                    dense_scores = self.embeddings @ emb.astype(np.float32)
                base_scores = fuse_scores(
                    dense_scores, lexical_scores, self.config.lexical_weight
                )
        return self._rank(
            query_vec, target_sentiment, None, artist, category, base_scores=base_scores
        )

    def recommend_by_lexical(self, text: str) -> list[Recommendation]:
        """Rank by lexical scores only, for use while the dense model is cold."""
        normalized = self.query_encoder.normalize_query(text)
        if not self.lexical.should_fuse(
            normalized,
            min_tokens=self.config.lexical_min_tokens,
            short_idf=self.config.lexical_short_idf,
        ):
            return []
        lexical_scores = self.lexical.song_scores(normalized)
        if lexical_scores.max() <= 0:
            return []
        return self._rank(None, None, None, None, None, base_scores=lexical_scores)

    def normalized_query(self, text: str) -> str:
        return self.query_encoder.normalize_query(text)
