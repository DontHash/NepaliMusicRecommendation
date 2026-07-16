"""Audit and clean lyrics CSV into music_rec_artifacts/cleaned_lyrics.csv."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import asdict, dataclass, field

import pandas as pd

from .config import Config
from .tokenization import indic_available, normalize_nfc, token_count


@dataclass
class AuditReport:
    total_rows: int = 0
    empty_lyrics: int = 0
    nfc_normalized: int = 0
    exact_duplicates: int = 0
    near_duplicates_same_title_artist: int = 0
    short_songs_removed: int = 0
    rows_after_cleaning: int = 0
    indic_nlp_used: bool = False
    token_count_min: int = 0
    token_count_median: float = 0.0
    token_count_max: int = 0
    notes: list[str] = field(default_factory=list)


def _needs_nfc(text: str) -> bool:
    return text != unicodedata.normalize("NFC", text)


def run_audit(config: Config | None = None) -> AuditReport:
    config = config or Config()
    df = pd.read_csv(config.raw_lyrics_csv, encoding="utf-8")
    report = AuditReport(total_rows=len(df), indic_nlp_used=indic_available())

    lyrics_col = "lyrics_devanagari" if "lyrics_devanagari" in df.columns else "Lyrics"
    title_col = "title_clean" if "title_clean" in df.columns else "Title"
    artist_col = "artist_clean" if "artist_clean" in df.columns else "Artist"

    df[lyrics_col] = df[lyrics_col].fillna("").astype(str)

    report.nfc_normalized = int(df[lyrics_col].map(_needs_nfc).sum())
    df[lyrics_col] = df[lyrics_col].map(normalize_nfc)
    df[title_col] = df[title_col].fillna("").astype(str).map(normalize_nfc)
    df[artist_col] = df[artist_col].fillna("").astype(str).map(normalize_nfc)

    empty_mask = df[lyrics_col].str.strip() == ""
    report.empty_lyrics = int(empty_mask.sum())
    df = df[~empty_mask].copy()

    before = len(df)
    df = df.drop_duplicates(subset=[lyrics_col], keep="first").copy()
    report.exact_duplicates = before - len(df)

    before = len(df)
    df = df.drop_duplicates(subset=[title_col, artist_col], keep="first").copy()
    report.near_duplicates_same_title_artist = before - len(df)

    df["token_count"] = df[lyrics_col].map(token_count)
    short_mask = df["token_count"] < config.min_tokens
    report.short_songs_removed = int(short_mask.sum())
    df = df[~short_mask].copy()

    df = df.reset_index(drop=True)
    df.insert(0, "song_id", range(len(df)))

    out = pd.DataFrame(
        {
            "song_id": df["song_id"],
            "title": df[title_col],
            "artist": df[artist_col],
            "category": df.get("category", ""),
            "lyrics": df[lyrics_col],
            "token_count": df["token_count"],
        }
    )
    out.to_csv(config.cleaned_lyrics_csv, index=False, encoding="utf-8")

    report.rows_after_cleaning = len(out)
    report.token_count_min = int(out["token_count"].min())
    report.token_count_median = float(out["token_count"].median())
    report.token_count_max = int(out["token_count"].max())
    if not indic_available():
        report.notes.append("indic-nlp-library not available; used regex Devanagari tokenizer.")

    config.audit_report_json.write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    rep = run_audit()
    print(json.dumps(asdict(rep), ensure_ascii=False, indent=2))
