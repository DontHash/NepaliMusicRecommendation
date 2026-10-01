"""Central configuration: paths and model names for the recommender."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

logger = logging.getLogger(__name__)

# Serving attributes resolved through a published version manifest.
# Offline producers must call force_staging() and write the staging layout.
ARTIFACT_ATTR_NAMES: dict[str, str] = {
    "cleaned_lyrics_csv": "cleaned_lyrics",
    "embedding_ids_json": "embedding_ids",
    "embeddings_npy": "embeddings",
    "window_vectors_npy": "window_vectors",
    "window_owners_npy": "window_owners",
    "sentiment_scores_csv": "sentiment_scores",
    "mood_probe_npz": "mood_probe",
    "feature_matrix_npy": "feature_matrix",
    "faiss_index_path": "lyrics_index",
    "audio_embeddings_npy": "audio_embeddings",
    "audio_embedding_keys_csv": "audio_embedding_keys",
    "audio_track_matches_csv": "audio_track_matches",
}


def force_staging() -> None:
    """Offline producers read and write the staging layout, never a published set."""
    os.environ["PROJECTR_ARTIFACTS_DISABLE"] = "1"


@dataclass
class Config:
    project_root: Path = PROJECT_ROOT

    raw_lyrics_csv: Path = PROJECT_ROOT / "CSVs Dataset" / "Lyrics_Dataset_final.csv"
    transliterator_checkpoint: Path = PROJECT_ROOT / "new_char_transformer_domain.pt"
    transliterator_vocab: Path = PROJECT_ROOT / "new_char_vocab.pkl"
    artifacts_dir: Path = PROJECT_ROOT / "music_rec_artifacts"

    cleaned_lyrics_csv: Path = field(init=False)
    audit_report_json: Path = field(init=False)
    corpus_typo_map_csv: Path = field(init=False)
    corpus_typo_map_enabled: bool = True
    embeddings_npy: Path = field(init=False)
    embedding_ids_json: Path = field(init=False)
    embedding_onnx_dir: Path = field(init=False)
    window_vectors_npy: Path = field(init=False)
    window_owners_npy: Path = field(init=False)
    sentiment_scores_csv: Path = field(init=False)
    sentiment_model_dir: Path = field(init=False)
    mood_probe_npz: Path = field(init=False)
    feature_matrix_npy: Path = field(init=False)
    faiss_index_path: Path = field(init=False)
    metadata_parquet: Path = field(init=False)
    audio_dir: Path = field(init=False)
    audio_embeddings_npy: Path = field(init=False)
    audio_embedding_keys_csv: Path = field(init=False)
    audio_track_matches_csv: Path = field(init=False)
    window_index_path: Path = field(init=False)
    lexical_cache_path: Path = field(init=False)

    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    embedding_device: str = field(
        default_factory=lambda: os.environ.get("PROJECTR_EMBED_DEVICE", "auto")
    )
    embedding_backend: str = field(
        default_factory=lambda: os.environ.get("PROJECTR_EMBED_BACKEND", "auto")
    )
    sentiment_base_model: str = "google/muril-base-cased"

    min_tokens: int = 10
    embed_batch_size: int = 32
    embed_batch_size_gpu: int = 128
    embed_chunking: bool = True
    embed_window_tokens: int = 48
    embed_window_stride: int = 24
    sentiment_max_len: int = 256
    sentiment_epochs: int = 2
    sentiment_labels: tuple[str, ...] = ("negative", "neutral", "positive")

    ann_top_k: int = 50
    final_top_k: int = 10
    mmr_lambda: float = 0.7
    sentiment_weight: float = 0.15
    lexical_enabled: bool = True
    lexical_weight: float = 0.65
    lexical_min_tokens: int = 3
    lexical_short_idf: float = 2.5
    lexical_fuzzy_enabled: bool = True
    lexical_fuzzy_max_df: int = 10
    lexical_fuzzy_threshold: float = 70.0
    lexical_fuzzy_weight: float = 0.8
    lexical_fuzzy_max_candidates: int = 3
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    dedup_enabled: bool = True
    use_window_search: bool = True
    probe_positive_threshold: float = 0.0
    probe_negative_threshold: float = 0.10
    audio_enabled: bool = True
    audio_weight: float = 0.5

    # --- scale knobs ---------------------------------------------------------
    # auto: exact IndexFlatIP below 50k vectors, HNSW above (PROJECTR_INDEX).
    index_type: str = field(default_factory=lambda: os.environ.get("PROJECTR_INDEX", "auto"))
    index_hnsw_m: int = 32
    index_ef_construction: int = 200
    index_ef_search: int = 64
    # window ANN switches on only where exact matmul stops fitting (PROJECTR_WINDOW_ANN).
    window_ann: str = field(default_factory=lambda: os.environ.get("PROJECTR_WINDOW_ANN", "auto"))
    window_ann_threshold: int = 250_000
    window_ann_top_k: int = 2000
    # Persisted sparse lexical index (avoids the per-process BM25 rebuild).
    lexical_cache_enabled: bool = True
    # Bounded query-embedding cache (repeat queries skip the encoder).
    query_cache_size: int = 512

    def __post_init__(self):
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.cleaned_lyrics_csv = self.artifacts_dir / "cleaned_lyrics.csv"
        self.audit_report_json = self.artifacts_dir / "audit_report.json"
        self.corpus_typo_map_csv = PROJECT_ROOT / "eval" / "corpus_typo_map.csv"
        self.embeddings_npy = self.artifacts_dir / "embeddings.npy"
        self.embedding_ids_json = self.artifacts_dir / "embedding_ids.json"
        self.embedding_onnx_dir = self.artifacts_dir / "embedding_onnx"
        self.window_vectors_npy = self.artifacts_dir / "window_vectors.npy"
        self.window_owners_npy = self.artifacts_dir / "window_owners.npy"
        self.sentiment_scores_csv = self.artifacts_dir / "sentiment_scores.csv"
        self.sentiment_model_dir = self.artifacts_dir / "sentiment_model"
        self.mood_probe_npz = self.artifacts_dir / "mood_probe.npz"
        self.feature_matrix_npy = self.artifacts_dir / "feature_matrix.npy"
        self.faiss_index_path = self.artifacts_dir / "lyrics.faiss"
        self.metadata_parquet = self.artifacts_dir / "song_metadata.csv"
        self.audio_dir = PROJECT_ROOT / "R_data" / "audio"
        self.audio_embeddings_npy = self.audio_dir / "audio_embeddings.npy"
        self.audio_embedding_keys_csv = self.audio_dir / "audio_embedding_keys.csv"
        self.audio_track_matches_csv = self.audio_dir / "audio_track_matches.csv"
        self.window_index_path = self.artifacts_dir / "window_index.faiss"
        self.lexical_cache_path = self.artifacts_dir / "lexical_cache.pkl"
        self.artifact_source = "staging"
        self.artifact_version: str | None = None
        self._resolve_published_artifacts()

    def _resolve_published_artifacts(self) -> None:
        """Re-point serving artifact attributes at the published version, if any.

        The pointer (``PROJECTR_ARTIFACTS_POINTER`` or ``<artifacts>/current.json``)
        names a version directory whose manifest maps artifact names to paths.
        Missing/invalid pointers fall back to the staging layout, so a fresh
        checkout works before its first publish. ``PROJECTR_ARTIFACTS_DISABLE=1``
        forces staging (offline producers use force_staging()).
        """
        if os.environ.get("PROJECTR_ARTIFACTS_DISABLE") == "1":
            return
        pointer_path = Path(os.environ.get(
            "PROJECTR_ARTIFACTS_POINTER", self.artifacts_dir / "current.json"))
        try:
            pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
            version = str(pointer["version"])
            version_dir = pointer_path.parent / "versions" / version
            manifest = json.loads((version_dir / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError, KeyError):
            return
        relative_paths = {entry["name"]: entry["path"] for entry in manifest.get("artifacts", [])
                          if not entry.get("missing") and "path" in entry}
        for attribute, name in ARTIFACT_ATTR_NAMES.items():
            relative = relative_paths.get(name)
            if relative:
                setattr(self, attribute, version_dir / relative)
        self.artifact_source = f"published:{version}"
        self.artifact_version = version
        logger.info("serving artifacts from published version %s", version)
