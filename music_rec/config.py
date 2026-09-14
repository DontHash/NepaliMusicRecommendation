"""Central configuration: paths and model names for the recommender."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Config:
    project_root: Path = PROJECT_ROOT

    raw_lyrics_csv: Path = PROJECT_ROOT / "CSVs Dataset" / "Lyrics_Dataset_final.csv"
    transliterator_checkpoint: Path = PROJECT_ROOT / "new_char_transformer_best.pt"
    transliterator_vocab: Path = PROJECT_ROOT / "new_char_vocab.pkl"
    artifacts_dir: Path = PROJECT_ROOT / "music_rec_artifacts"

    cleaned_lyrics_csv: Path = field(init=False)
    audit_report_json: Path = field(init=False)
    embeddings_npy: Path = field(init=False)
    embedding_ids_json: Path = field(init=False)
    sentiment_scores_csv: Path = field(init=False)
    sentiment_model_dir: Path = field(init=False)
    feature_matrix_npy: Path = field(init=False)
    faiss_index_path: Path = field(init=False)
    metadata_parquet: Path = field(init=False)

    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    sentiment_base_model: str = "google/muril-base-cased"

    min_tokens: int = 10
    embed_batch_size: int = 32
    sentiment_max_len: int = 256
    sentiment_epochs: int = 2
    sentiment_labels: tuple[str, ...] = ("negative", "neutral", "positive")

    ann_top_k: int = 50
    final_top_k: int = 10
    mmr_lambda: float = 0.7
    sentiment_weight: float = 0.15

    def __post_init__(self):
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.cleaned_lyrics_csv = self.artifacts_dir / "cleaned_lyrics.csv"
        self.audit_report_json = self.artifacts_dir / "audit_report.json"
        self.embeddings_npy = self.artifacts_dir / "embeddings.npy"
        self.embedding_ids_json = self.artifacts_dir / "embedding_ids.json"
        self.sentiment_scores_csv = self.artifacts_dir / "sentiment_scores.csv"
        self.sentiment_model_dir = self.artifacts_dir / "sentiment_model"
        self.feature_matrix_npy = self.artifacts_dir / "feature_matrix.npy"
        self.faiss_index_path = self.artifacts_dir / "lyrics.faiss"
        self.metadata_parquet = self.artifacts_dir / "song_metadata.csv"
