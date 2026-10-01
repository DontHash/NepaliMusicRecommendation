"""The ProjectR asset graph: names, dependencies and actions.

All producers run against the staging layout (``force_staging``); publishing
snapshots the staging files into a versioned, verified artifact set.
"""

from __future__ import annotations

from pathlib import Path

from pipelines.core import PROJECT_ROOT, Asset, RunContext, script_action
from pipelines.runner import Pipeline

# --- library-backed actions --------------------------------------------------


def _corpus_clean(context: RunContext) -> dict:
    from dataclasses import asdict

    from music_rec.data_audit import run_audit

    report = asdict(run_audit(context.config))
    return {key: value for key, value in report.items()
            if isinstance(value, (int, float, str, bool))}


def _corpus_embed(context: RunContext) -> dict:
    from music_rec.embeddings import compute_embeddings

    vectors = compute_embeddings(context.config)
    return {"songs": int(vectors.shape[0]), "dim": int(vectors.shape[1])}


def _features(context: RunContext) -> dict:
    from music_rec.features import build_feature_matrix

    matrix = build_feature_matrix(context.config)
    return {"rows": int(matrix.shape[0]), "dim": int(matrix.shape[1])}


def _index_songs(context: RunContext) -> dict:
    import numpy as np

    from music_rec.index import build_index, index_kind

    config = context.config
    source = (config.feature_matrix_npy if config.feature_matrix_npy.exists()
              else config.embeddings_npy)
    vectors = np.load(source)
    index = build_index(
        vectors,
        config.faiss_index_path,
        index_type=config.index_type,
        hnsw_m=config.index_hnsw_m,
        ef_construction=config.index_ef_construction,
        ef_search=config.index_ef_search,
    )
    return {"type": index_kind(index), "vectors": int(vectors.shape[0]),
            "source": Path(source).name}


def _index_windows(context: RunContext) -> dict:
    import numpy as np

    from music_rec.window_search import ann_enabled, build_window_index

    config = context.config
    if not (config.window_vectors_npy.exists() and config.window_owners_npy.exists()):
        return {"enabled": False, "reason": "window artifacts absent"}
    n_windows = int(np.load(config.window_owners_npy, mmap_mode="r").shape[0])
    if not ann_enabled(config.window_ann, n_windows, config.window_ann_threshold):
        return {"enabled": False, "windows": n_windows, "reason": "below auto threshold"}
    build_window_index(
        config.window_vectors_npy,
        config.window_index_path,
        hnsw_m=config.index_hnsw_m,
        ef_construction=config.index_ef_construction,
        ef_search=config.index_ef_search,
    )
    return {"enabled": True, "windows": n_windows}


def _publish(context: RunContext) -> dict:
    from data_engineering.publish import default_pointer_path, publish_artifacts

    result = publish_artifacts(context.project_root,
                               default_pointer_path(context.project_root),
                               config=context.config)
    return {"version": result["version"], "artifacts": len(result["copied"]),
            "bytes": result["bytes"]}


def _corpus_append(context: RunContext) -> dict:
    from music_rec.incremental import append_new_songs

    report = append_new_songs(
        context.config,
        report_path=context.project_root / "R_data" / "audio" / "text_artifacts_update_report.json",
    )
    return {"status": report["status"], "new_songs": report.get("new_songs", 0),
            "songs_after": report.get("songs_after", 0)}


# --- script-backed actions ---------------------------------------------------

_mood_probe = script_action(
    "scripts/train_mood_probe.py",
    "--pseudo", "R_data/raw/gemini/corpus_v3/labels_merged.csv",
    "--probe-out", "music_rec_artifacts/mood_probe.npz",
    "--scores-out", "music_rec_artifacts/sentiment_scores.csv",
)
_mood_vectors = script_action("scripts/build_mood_vectors.py")
_audio_manifest = script_action("scripts/audio/build_manifest.py")
_audio_lyrics = script_action("scripts/audio/fetch_lyrics.py")
_audio_dataset_lines = script_action("scripts/audio/build_dataset_lines.py")
_audio_embeddings = script_action("scripts/audio/embed_audio.py")
_audio_similarity = script_action("scripts/audio/analyze_audio_similarity.py")
_corpus_v3 = script_action("scripts/audio/merge_into_corpus.py")


def build_pipeline(*, project_root: Path = PROJECT_ROOT, state_dir: Path | None = None,
                   config=None) -> Pipeline:
    if config is None:
        from music_rec.config import Config, force_staging

        force_staging()
        config = Config()

    assets = [
        Asset("corpus.source", external=True,
              outputs=("CSVs Dataset/Lyrics_Dataset_final.csv",),
              description="scraped lyrics dataset (not regenerable by this repo)"),
        Asset("corpus.clean", action=_corpus_clean, deps=("corpus.source",),
              outputs=("music_rec_artifacts/cleaned_lyrics.csv",),
              description="audit + clean the raw lyrics dataset"),
        Asset("corpus.embed", action=_corpus_embed, deps=("corpus.clean",),
              outputs=("music_rec_artifacts/embeddings.npy",
                       "music_rec_artifacts/embedding_ids.json",
                       "music_rec_artifacts/window_vectors.npy",
                       "music_rec_artifacts/window_owners.npy"),
              description="chunked lyric embeddings + windows"),
        Asset("labels.gemini", external=True,
              outputs=("R_data/raw/gemini/corpus_v3/labels_merged.csv",),
              description="LLM teacher labels (produced off-repo)"),
        Asset("mood.probe", action=_mood_probe, deps=("corpus.embed", "labels.gemini"),
              outputs=("music_rec_artifacts/mood_probe.npz",
                       "music_rec_artifacts/sentiment_scores.csv",
                       "music_rec_artifacts/mood_probe_report.json"),
              description="linear mood probe + per-song scores"),
        Asset("mood.vectors", action=_mood_vectors, deps=("mood.probe",),
              outputs=("music_rec_artifacts/mood_vectors.csv",),
              description="slim joy/sadness/anger vectors for browsing"),
        Asset("features", action=_features,
              deps=("corpus.embed", "mood.probe", "mood.vectors"),
              outputs=("music_rec_artifacts/feature_matrix.npy",
                       "music_rec_artifacts/feature_meta.json"),
              description="serving feature matrix (embeddings + sentiment + metadata)"),
        Asset("index.songs", action=_index_songs, deps=("features",),
              outputs=("music_rec_artifacts/lyrics.faiss",),
              description="song ANN index"),
        Asset("index.windows", action=_index_windows, deps=("corpus.embed",),
              description="optional window ANN side-index (auto threshold)"),
        Asset("audio.collection", external=True,
              description="local audio library (PROJECTR_AUDIO_COLLECTION)"),
        Asset("audio.manifest", action=_audio_manifest,
              deps=("audio.collection", "corpus.clean"),
              outputs=("R_data/audio/audio_manifest.csv", "R_data/audio/audio_tracks.csv"),
              description="per-file + per-track manifest and metadata match"),
        Asset("audio.lyrics", action=_audio_lyrics, deps=("audio.manifest",),
              outputs=("R_data/audio/audio_lyrics.jsonl",),
              description="resumable lyrics fetch (LRCLIB + fallbacks)"),
        Asset("audio.dataset_lines", action=_audio_dataset_lines,
              deps=("audio.lyrics", "corpus.clean"),
              outputs=("R_data/audio/audio_track_matches.csv",
                       "R_data/audio/audio_file_map.csv",
                       "R_data/audio/audio_new_songs_v2.csv"),
              description="lyrics confirmation + new dataset lines"),
        Asset("audio.embeddings", action=_audio_embeddings, deps=("audio.manifest",),
              outputs=("R_data/audio/audio_embedding_keys.csv",
                       "R_data/audio/audio_embeddings.npy"),
              description="CLAP audio embeddings (resumable)"),
        Asset("audio.similarity", action=_audio_similarity, deps=("audio.embeddings",),
              outputs=("R_data/audio/audio_duplicate_candidates.csv",),
              description="audio near-duplicate candidates"),
        Asset("corpus.v3", action=_corpus_v3,
              deps=("audio.dataset_lines", "corpus.clean"),
              outputs=("CSVs Dataset/corpus_final_v3.csv",
                       "R_data/audio/merge_report_v3.json"),
              description="merge audio-derived lines into the corpus"),
        Asset("corpus.refresh", action=_corpus_append, deps=("corpus.v3", "corpus.embed"),
              outputs=("R_data/audio/text_artifacts_update_report.json",),
              description="append new songs to embeddings/probe/features/index (incremental)"),
        Asset("publish.artifacts", action=_publish,
              deps=("features", "index.songs", "index.windows", "mood.vectors",
                    "corpus.refresh"),
              outputs=("music_rec_artifacts/artifact_manifest.json",
                       "music_rec_artifacts/current.json"),
              description="verified snapshot + atomic serving pointer"),
    ]
    return Pipeline(assets, project_root=project_root, state_dir=state_dir, config=config)
