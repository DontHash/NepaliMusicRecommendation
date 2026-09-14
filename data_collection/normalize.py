"""Normalization helpers: dedupe keys, lyric hashes, script detection."""

from __future__ import annotations

import hashlib
import re
import unicodedata

from lyrics_pipeline.patterns import DEVANAGARI_RE, ROMAN_RE

_WS_RE = re.compile(r"\s+")
_NON_WORD_RE = re.compile(r"[^\w\u0900-\u097F]+", re.UNICODE)


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text or "")


def fold(text: str) -> str:
    text = nfc(text).casefold()
    text = _NON_WORD_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


def make_dedupe_key(artist: str, title: str, duration_s: int | None = None) -> str:
    bucket = "" if not duration_s or duration_s <= 0 else str(int(duration_s) // 5)
    return f"{fold(artist)}|{fold(title)}|{bucket}"


def lyrics_sha(lyrics: str) -> str:
    normalized = _WS_RE.sub(" ", nfc(lyrics)).strip().casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def detect_script(text: str) -> str:
    has_dev = bool(DEVANAGARI_RE.search(text or ""))
    has_roman = bool(ROMAN_RE.search(text or ""))
    if has_dev and has_roman:
        return "mixed"
    if has_dev:
        return "devanagari"
    if has_roman:
        return "romanized"
    return "unknown"
