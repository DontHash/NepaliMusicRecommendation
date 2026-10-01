"""Shared helpers for the audio <-> lyrics pipeline (ProjectR)."""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audio import config  # noqa: E402

COLLECTION_ROOT = config.COLLECTION_ROOT
AUDIO_DATA_DIR = config.AUDIO_DATA_DIR
AUDIO_EXTS = config.AUDIO_EXTS

JUNK_PATTERNS = [
    r"\(official[^)]*\)", r"\[official[^\]]*\]", r"\(lyric[^)]*\)", r"\[lyric[^\]]*\]",
    r"\(audio[^)]*\)", r"\[audio[^\]]*\]", r"\(video[^)]*\)", r"\[video[^\]]*\]",
    r"\(full[^)]*\)", r"\[full[^\]]*\]", r"\(hd[^)]*\)", r"\[hd[^\]]*\]",
    r"official\s+music\s+video", r"lyrical\s+video", r"lyrics\s+video", r"music\s+video",
    r"full\s+song", r"new\s+nepali\s+song", r"nepali\s+song", r"nepali\s+rap\s+song",
    r"prod\.?\s*by[^|]*", r"\bprod\b[^|]*", r"www\.[^\s]+", r"https?://\S+",
    r"\(\s*\d{4}\s*\)", r"\b(19|20)\d{2}\b", r"\b\d{3,}p\b", r"\b\dx\d+\b",
    r"\bremix\b", r"\bcover\b", r"\blive\b", r"\bfree\s+download\b", r"\bdownload\b",
    r"\(2\)", r"\(\d+\)", r"\[\d+\]",
]
_GENERIC_TITLES = {
    "aama", "aamaa", "aafno", "maya", "timi", "ma", "mann", "man", "sathi", "saathi",
    "yaad", "prem", "sapana", "akash", "aakash", "sansar", "jindagi", "jiban",
    "kahani", "katha", "gita", "geet", "song", "music", "instrumental", "hits",
    "best", "old", "new", "nepali", "sad", "love", "trap", "beat", "beats",
}


def strip_junk(text: str) -> str:
    text = str(text or "")
    # Uploader-style titles: keep only the first pipe-separated segment.
    text = re.split(r"\s*[|｜]\s*", text, maxsplit=1)[0]
    for pattern in JUNK_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    return text.strip()


LRC_LINE_RE = re.compile(r"^\[\d{1,2}:\d{2}(?:\.\d{1,3})?\]\s?")
CJK_CREDIT_RE = re.compile(r"作词|作曲|编曲|混音|制作人|录音|母带|出品|演唱")
CJK_RE = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def sanitize_provider_lyrics(text: str) -> str:
    """Drop LRC timestamps and CJK credit/translation lines from provider output."""
    lines: list[str] = []
    for line in str(text or "").splitlines():
        line = LRC_LINE_RE.sub("", line).strip()
        if not line:
            continue
        if CJK_CREDIT_RE.search(line):
            continue
        if CJK_RE.search(line) and not DEVANAGARI_RE.search(line):
            continue
        lines.append(line)
    return "\n".join(lines)


def devanagari_share(text: str) -> float:
    chars = [ch for ch in str(text or "") if not ch.isspace()]
    if not chars:
        return 0.0
    return sum(1 for ch in chars if DEVANAGARI_RE.match(ch)) / len(chars)


_ROMAN_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'’]*$")


def nepali_ratio(text: str) -> float:
    """Fraction of lyric lines that read as Nepali (Devanagari or romanized).

    Uses the transliterator's English-gate logic on the *raw* provider text:
    a line is English when it has >=4 roman tokens, >=3 English function words
    and no Nepali function words. This distinguishes English songs from
    romanized Nepali, which a Devanagari-share check cannot do after
    transliteration. Empty input -> 1.0 (unknown, do not reject).
    """
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    if not lines:
        return 1.0
    from lyrics_pipeline.transliterator import ENGLISH_FUNCTION_WORDS, NEPALI_FUNCTION_WORDS

    nepali = english = 0
    for line in lines:
        if DEVANAGARI_RE.search(line):
            nepali += 1
            continue
        tokens = [token.lower() for token in line.split() if _ROMAN_TOKEN_RE.match(token)]
        if len(tokens) < 4:
            continue
        english_hits = sum(1 for token in tokens if token in ENGLISH_FUNCTION_WORDS)
        nepali_hits = sum(1 for token in tokens if token in NEPALI_FUNCTION_WORDS)
        if english_hits >= 3 and nepali_hits == 0:
            english += 1
        elif nepali_hits > 0:
            nepali += 1
    total = nepali + english
    return nepali / total if total else 1.0


def git_sha() -> str:
    """Best-effort current commit for artifact provenance."""
    import subprocess

    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:  # noqa: BLE001 - provenance is best-effort
        return ""


def sha256_file(path) -> str:
    import hashlib

    try:
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return ""


def normalize_text(text: str) -> str:
    """Lowercase, strip punctuation/junk, collapse whitespace. Keeps Devanagari."""
    text = unicodedata.normalize("NFC", str(text or ""))
    text = strip_junk(text)
    text = text.lower()
    text = re.sub(r"[^\w\u0900-\u097F]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def primary_artist(text: str) -> str:
    """First credited artist; drops '&', ',', 'feat', 'ft', ' x ' collaborators."""
    text = str(text or "").strip()
    for pattern in (r"\s+feat\.?\s+", r"\s+ft\.?\s+", r"\s+x\s+", r"\s*&\s*", r"\s*,\s*"):
        text = re.split(pattern, text, maxsplit=1, flags=re.IGNORECASE)[0]
    return text.strip()


def track_key(artist: str, title: str) -> str:
    return f"{normalize_text(artist)}|{normalize_text(title)}"


def parse_filename(name: str) -> tuple[str, str]:
    stem = Path(name).stem
    stem = re.sub(r"\.(mp3|m4a|ogg|wav|flac|opus|aac|3gpp|webm)$", "", stem, flags=re.IGNORECASE)
    for separator in (" - ", " – ", " — "):
        if separator in stem:
            left, right = stem.split(separator, 1)
            if right.strip():
                return left.strip(), right.strip()
    return "", stem.strip()


def is_generic_title(title: str) -> bool:
    normalized = normalize_text(title)
    return len(normalized.split()) < 2 or normalized in _GENERIC_TITLES


def load_corpus():
    import pandas as pd

    from music_rec.config import Config

    frame = pd.read_csv(Config().cleaned_lyrics_csv, encoding="utf-8").fillna("")
    frame["norm_title"] = frame["title"].map(normalize_text)
    frame["norm_artist"] = frame["artist"].map(normalize_text)
    return frame


def sentence_shingles(text: str, size: int = 4) -> set[str]:
    tokens = normalize_text(text).split()
    return {" ".join(tokens[i : i + size]) for i in range(max(len(tokens) - size + 1, 0))}


def lyrics_similarity(left: str, right: str) -> float:
    """0-100 blend of token-set similarity and 4-gram shingle Jaccard."""
    from rapidfuzz import fuzz

    a, b = normalize_text(left), normalize_text(right)
    if len(a) < 20 or len(b) < 20:
        return 0.0
    token_score = float(fuzz.token_set_ratio(a, b))
    set_a, set_b = sentence_shingles(a), sentence_shingles(b)
    union = set_a | set_b
    jaccard = (len(set_a & set_b) / len(union) * 100.0) if union else 0.0
    return round(0.7 * token_score + 0.3 * jaccard, 2)


_PIPELINE = None


def get_pipeline():
    """Lazy singleton of the production cleaning+transliteration pipeline."""
    global _PIPELINE
    if _PIPELINE is None:
        from lyrics_pipeline.pipeline import LyricsCleaningPipeline
        from lyrics_pipeline.transliterator import NepaliTransliterator

        _PIPELINE = LyricsCleaningPipeline(transliterator=NepaliTransliterator())
    return _PIPELINE


def process_lyrics(text: str, *, title: str, artist: str, category: str = "nepali",
                   source: str = "", stage: str = "", source_url: str = "") -> dict:
    """Clean + transliterate raw lyrics, returning V2-corpus-shaped fields."""
    result = get_pipeline().process_row(
        {"Category": category, "Title": title, "Artist": artist, "Lyrics": text},
        extras={"source": source, "stage": stage, "source_url": source_url},
    )
    return {
        "title_clean": result.title_clean,
        "artist_clean": result.artist_clean,
        "lyrics_devanagari": result.lyrics_devanagari,
        "line_count": result.line_count,
        "char_count": result.char_count,
        "script_style_original": result.script_style_original,
        "script_style_cleaned": result.script_style_cleaned,
        "transliterated": int(result.transliterated),
        "cleaning_actions": result.cleaning_actions,
    }
