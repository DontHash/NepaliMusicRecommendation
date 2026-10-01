"""Canonical dataset contracts for ProjectR.

Every committed dataset has one declared schema here: column dtypes, nullability,
allowed values, ranges and keys. The validator (``data_engineering.validate``)
enforces them in tests and CI, so a malformed dataset fails the build instead of
silently poisoning downstream artifacts.

Bump a schema's ``version`` whenever its contract changes; artifacts record the
versions they were validated against.
"""

from __future__ import annotations

from dataclasses import dataclass, field

INT = "int"
FLOAT = "float"
STR = "str"
BOOL = "bool"


@dataclass(frozen=True)
class Column:
    dtype: str
    required: bool = True
    nullable: bool = False
    allowed: frozenset | None = None
    minimum: float | None = None
    maximum: float | None = None
    pattern: str | None = None
    strip: bool = False  # whitespace-only strings count as null


@dataclass(frozen=True)
class Schema:
    name: str
    version: int
    columns: dict[str, Column]
    primary_key: str | None = None
    description: str = ""


_MOOD_FLAG = Column(INT, allowed=frozenset({0, 1}))
_SENTIMENT_LABEL = Column(STR, allowed=frozenset({"positive", "negative", "neutral"}))
_ID_PATTERN = r"^\d+$"
_NEW_ID_PATTERN = r"^A-[0-9a-f]{10}$"
_MATCH_BASIS = frozenset({
    "metadata_only", "metadata_candidate", "no_lyrics", "lyrics_confirmed",
    "lyrics_ambiguous_linked", "new_lyrics", "new_lyrics_non_nepali",
    "new_lyrics_too_short",
})
_METADATA_MATCH = frozenset({"strong", "probable", "weak", "none"})

SCHEMAS: dict[str, Schema] = {
    "cleaned_lyrics": Schema(
        name="cleaned_lyrics",
        version=1,
        description="Model corpus (music_rec_artifacts/cleaned_lyrics.csv); song_id is stable.",
        primary_key="song_id",
        columns={
            "song_id": Column(INT, minimum=0),
            "title": Column(STR, nullable=True),
            "artist": Column(STR, nullable=True),
            "category": Column(STR, nullable=True),
            "lyrics": Column(STR, strip=True),
            "token_count": Column(INT, minimum=1),
        },
    ),
    "corpus_rows": Schema(
        name="corpus_rows",
        version=1,
        description="Versioned corpus source file (CSVs Dataset/corpus_final_v*.csv).",
        columns={
            "category": Column(STR, nullable=True),
            "title_clean": Column(STR, nullable=True),
            "artist_clean": Column(STR, nullable=True),
            "lyrics_devanagari": Column(STR, nullable=True),
            "line_count": Column(INT, minimum=0),
            "char_count": Column(INT, minimum=0),
            "script_style_original": Column(STR, nullable=True),
            "script_style_cleaned": Column(STR, nullable=True),
            "transliterated": Column(INT, allowed=frozenset({0, 1})),
            "source": Column(STR, nullable=True),
            "stage": Column(STR, nullable=True),
            "source_url": Column(STR, nullable=True),
        },
    ),
    "mood_labels": Schema(
        name="mood_labels",
        version=1,
        description="Gemini teacher labels (R_data/raw/gemini/**/labels_merged.csv).",
        primary_key="song_id",
        columns={
            "song_id": Column(INT, minimum=0),
            "positive": _MOOD_FLAG,
            "negative": _MOOD_FLAG,
            "joy": _MOOD_FLAG,
            "sadness": _MOOD_FLAG,
            "anger": _MOOD_FLAG,
            "fear": _MOOD_FLAG,
            "depression": _MOOD_FLAG,
            "mood_phrase": Column(STR, nullable=True),
            "confidence": Column(STR, nullable=True),
        },
    ),
    "sentiment_scores": Schema(
        name="sentiment_scores",
        version=1,
        description="Installed mood probe outputs (music_rec_artifacts/sentiment_scores.csv).",
        primary_key="song_id",
        columns={
            "song_id": Column(INT, minimum=0),
            "joy": Column(FLOAT, minimum=0.0, maximum=1.0),
            "sadness": Column(FLOAT, minimum=0.0, maximum=1.0),
            "anger": Column(FLOAT, minimum=0.0, maximum=1.0),
            "fear": Column(FLOAT, minimum=0.0, maximum=1.0),
            "depression": Column(FLOAT, minimum=0.0, maximum=1.0),
            "positive": Column(FLOAT, minimum=0.0, maximum=1.0),
            "negative": Column(FLOAT, minimum=0.0, maximum=1.0),
            "sentiment_score": Column(FLOAT, minimum=-1.0, maximum=1.0),
            "sentiment_label": _SENTIMENT_LABEL,
        },
    ),
    "audio_tracks": Schema(
        name="audio_tracks",
        version=1,
        description="Unique tracks of the local audio collection + metadata match (R_data/audio/audio_tracks.csv).",
        primary_key="track_key",
        columns={
            "track_key": Column(STR, strip=True),
            "artist": Column(STR, nullable=True),
            "title": Column(STR, strip=True),
            "duration_s": Column(FLOAT, minimum=0.0),
            "n_files": Column(INT, minimum=1),
            "files": Column(STR, nullable=True),
            "source_query": Column(STR, nullable=True),
            "cand_song_id": Column(STR, nullable=True, pattern=_ID_PATTERN),
            "cand_title": Column(STR, nullable=True),
            "cand_artist": Column(STR, nullable=True),
            "title_score": Column(FLOAT, minimum=0.0, maximum=100.0),
            "artist_score": Column(FLOAT, minimum=0.0, maximum=100.0),
            "metadata_match": Column(STR, allowed=_METADATA_MATCH),
        },
    ),
    "audio_manifest": Schema(
        name="audio_manifest",
        version=1,
        description="One row per audio file (R_data/audio/audio_manifest.csv).",
        primary_key="audio_name",
        columns={
            "audio_name": Column(STR, strip=True),
            "audio_relpath": Column(STR, strip=True),
            "ext": Column(STR, strip=True),
            "bytes": Column(INT, minimum=0),
            "track_key": Column(STR, strip=True),
            "artist": Column(STR, nullable=True),
            "title": Column(STR, strip=True),
            "duration_s": Column(FLOAT, minimum=0.0, nullable=True),
            "source_query": Column(STR, nullable=True),
            "metadata_from": Column(STR, nullable=True),
            "cand_song_id": Column(STR, nullable=True, pattern=_ID_PATTERN),
            "cand_title": Column(STR, nullable=True),
            "cand_artist": Column(STR, nullable=True),
            "title_score": Column(FLOAT, minimum=0.0, maximum=100.0, nullable=True),
            "artist_score": Column(FLOAT, minimum=0.0, maximum=100.0, nullable=True),
            "metadata_match": Column(STR, allowed=_METADATA_MATCH, nullable=True),
        },
    ),
    "audio_track_matches": Schema(
        name="audio_track_matches",
        version=1,
        description="Audio track -> lyrics verdicts (R_data/audio/audio_track_matches.csv).",
        primary_key="track_key",
        columns={
            "track_key": Column(STR, strip=True),
            "artist": Column(STR, nullable=True),
            "title": Column(STR, strip=True),
            "duration_s": Column(FLOAT, minimum=0.0),
            "n_files": Column(INT, minimum=1),
            "files": Column(STR, nullable=True),
            "source_query": Column(STR, nullable=True),
            "cand_song_id": Column(STR, nullable=True, pattern=_ID_PATTERN),
            "cand_title": Column(STR, nullable=True),
            "cand_artist": Column(STR, nullable=True),
            "title_score": Column(FLOAT, minimum=0.0, maximum=100.0),
            "artist_score": Column(FLOAT, minimum=0.0, maximum=100.0),
            "metadata_match": Column(STR, allowed=_METADATA_MATCH),
            "match_song_id": Column(STR, nullable=True, pattern=_ID_PATTERN),
            "new_id": Column(STR, nullable=True, pattern=_NEW_ID_PATTERN),
            "match_basis": Column(STR, allowed=_MATCH_BASIS, nullable=True),
            "lyrics_sim": Column(FLOAT, minimum=0.0, maximum=100.0, nullable=True),
            "nepali_ratio": Column(FLOAT, minimum=0.0, maximum=1.0, nullable=True),
            "final_song_id": Column(STR, nullable=True, pattern=_ID_PATTERN),
        },
    ),
    "audio_file_map": Schema(
        name="audio_file_map",
        version=1,
        description="One row per audio file -> final song id (R_data/audio/audio_file_map.csv).",
        primary_key="audio_name",
        columns={
            "audio_name": Column(STR, strip=True),
            "audio_relpath": Column(STR, strip=True),
            "track_key": Column(STR, strip=True),
            "artist": Column(STR, nullable=True),
            "title": Column(STR, strip=True),
            "metadata_match": Column(STR, allowed=_METADATA_MATCH, nullable=True),
            "cand_song_id": Column(STR, nullable=True, pattern=_ID_PATTERN),
            "match_song_id": Column(STR, nullable=True, pattern=_ID_PATTERN),
            "new_id": Column(STR, nullable=True, pattern=_NEW_ID_PATTERN),
            "match_basis": Column(STR, allowed=_MATCH_BASIS, nullable=True),
            "final_song_id": Column(STR, nullable=True, pattern=_ID_PATTERN),
        },
    ),
    "audio_new_songs": Schema(
        name="audio_new_songs",
        version=1,
        description="New dataset lines discovered from audio (R_data/audio/audio_new_songs_v2.csv).",
        primary_key="audio_song_id",
        columns={
            "audio_song_id": Column(STR, pattern=r"A-[0-9a-f]{10}"),
            "track_key": Column(STR, strip=True),
            "audio_artist": Column(STR, nullable=True),
            "audio_title": Column(STR, strip=True),
            "duration_s": Column(FLOAT, minimum=0.0),
            "n_files": Column(INT, minimum=1),
            "lyrics_source": Column(STR, nullable=True),
            "source_url": Column(STR, nullable=True),
            "category": Column(STR, nullable=True),
            "title_clean": Column(STR, nullable=True),
            "artist_clean": Column(STR, nullable=True),
            "lyrics_devanagari": Column(STR, strip=True),
            "line_count": Column(INT, minimum=1),
            "char_count": Column(INT, minimum=1),
            "script_style_original": Column(STR, nullable=True),
            "script_style_cleaned": Column(STR, nullable=True),
            "transliterated": Column(INT, allowed=frozenset({0, 1})),
            "token_count": Column(INT, minimum=1),
        },
    ),
}


def get_schema(name: str) -> Schema:
    try:
        return SCHEMAS[name]
    except KeyError as exc:  # pragma: no cover - CLI path
        raise KeyError(f"unknown schema {name!r}; known: {', '.join(sorted(SCHEMAS))}") from exc
