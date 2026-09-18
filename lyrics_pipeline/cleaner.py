"""Lyrics text normalization and Genius metadata removal."""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable

from .patterns import (
    CONTRIBUTOR_LINE_RE,
    CONTRIBUTOR_PREFIX_RE,
    CRAWLER_FOOTER_PATTERNS,
    CREDIT_LINE_PATTERNS,
    DEVANAGARI_RE,
    EMBED_SUFFIX_RE,
    EMOJI_RE,
    GENIUS_ARTIST_MARKERS,
    HASHTAG_ONLY_RE,
    HASHTAG_RE,
    INVISIBLE_CHARS_RE,
    LYRICS_LABEL_RE,
    LYRICS_OF_RE,
    METADATA_LINE_PATTERNS,
    MUSIC_NOTE_RE,
    PAREN_ENGLISH_TRANSLATION_RE,
    QUOTE_MAP,
    ROMAN_RE,
    SECTION_BRACKET_RE,
    SECTION_WORD_RE,
    TITLE_JUNK_RE,
    TITLE_SUFFIX_RE,
    TRAILING_VIDEO_RE,
    TRANSLATIONS_HEADER_RE,
    URL_RE,
)
from .english_lexicon import (
    ENGLISH_DEVANAGARI_FORMS,
    METADATA_DEVANAGARI_FORMS,
    METADATA_WORDS,
)
from .template_blacklist import TEMPLATE_ARTIFACT_LINES


def normalize_unicode(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = INVISIBLE_CHARS_RE.sub("", text)
    text = text.translate(QUOTE_MAP)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def clean_title(title: str) -> str:
    title = normalize_unicode(title)
    match = LYRICS_OF_RE.match(title)
    if match:
        title = match.group(1).strip(" ,-–—")
    stripped = TITLE_JUNK_RE.sub("", title).strip(" ,-–—")
    if stripped:
        title = stripped
    title = TITLE_SUFFIX_RE.sub("", title).strip(" ,-–—")
    return title


def clean_artist(artist: str) -> str:
    artist = normalize_unicode(artist)
    artist = re.sub(r"\s+", " ", artist).strip()
    return artist


def _title_variants(title: str) -> set[str]:
    raw = normalize_unicode(title)
    base = clean_title(title)
    candidates = {raw, base}

    expanded: set[str] = set()
    for candidate in candidates:
        expanded.add(candidate)
        expanded.add(re.sub(r",?\s*nepali song\s*$", "", candidate, flags=re.IGNORECASE).strip())
        expanded.add(re.sub(r"\([^)]*\)", "", candidate).strip())
        expanded.add(re.sub(r"\s*-\s*.*$", "", candidate).strip())

    variants: set[str] = set()
    for candidate in expanded:
        if not candidate:
            continue
        lowered = candidate.lower()
        variants.add(lowered)
        variants.add(f"{lowered} lyrics")
        variants.add(f"{lowered} - lyrics")
    return {v.strip() for v in variants if v and v.strip()}


def _is_title_or_header_line(line: str, title: str) -> bool:
    normalized = _normalize_for_match(line)
    if normalized.endswith(" lyrics"):
        normalized = normalized[: -len(" lyrics")].strip()

    for variant in _title_variants(title):
        variant_norm = _normalize_for_match(variant)
        if normalized == variant_norm:
            return True
        if variant_norm and normalized.startswith(variant_norm):
            return True
        if variant_norm and variant_norm.startswith(normalized) and len(normalized) >= 4:
            return True
    return False


def _artist_variants(artist: str) -> set[str]:
    artist = clean_artist(artist)
    variants = {artist, artist.lower()}
    for part in re.split(r"\s*(?:,|&|feat\.?|ft\.?|aka)\s*", artist, flags=re.IGNORECASE):
        part = part.strip()
        if part:
            variants.add(part.lower())
    return variants


def _normalize_for_match(line: str) -> str:
    line = normalize_unicode(line).lower()
    line = re.sub(r"[^\w\s\u0900-\u097F]", " ", line)
    line = re.sub(r"\s+", " ", line).strip()
    return line


def _metadata_token_count(line: str) -> int:
    tokens = _normalize_for_match(line).split()
    return sum(
        1
        for token in tokens
        if token in METADATA_DEVANAGARI_FORMS or token in METADATA_WORDS
    )


def is_english_prose_line(line: str, min_tokens: int = 6, min_ratio: float = 0.7) -> bool:
    """Flag transliterated English lines such as blog prose or channel instructions.

    Only meaningful for text that already passed through the transliterator
    (English words became Devanagari); after the English gate is enabled the
    same content stays in Latin script and is handled by metadata patterns.
    """
    tokens = [token for token in line.split() if token]
    if len(tokens) < min_tokens:
        return False
    devanagari = 0
    english = 0
    for token in tokens:
        if not DEVANAGARI_RE.search(token):
            continue
        devanagari += 1
        if _normalize_for_match(token) in ENGLISH_DEVANAGARI_FORMS:
            english += 1
    if devanagari == 0:
        return False
    return english >= min_tokens and english / devanagari >= min_ratio


def is_noise_line(line: str, title: str, artist: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False

    if CONTRIBUTOR_LINE_RE.match(stripped):
        return True
    if TRANSLATIONS_HEADER_RE.match(stripped):
        return True
    if SECTION_BRACKET_RE.match(stripped):
        return True
    if SECTION_WORD_RE.match(stripped):
        return True

    for pattern in METADATA_LINE_PATTERNS:
        if pattern.match(stripped):
            return True

    for pattern in CREDIT_LINE_PATTERNS:
        if pattern.match(stripped):
            return True

    if LYRICS_LABEL_RE.search(stripped):
        return True

    if HASHTAG_ONLY_RE.match(stripped):
        return True

    for pattern in CRAWLER_FOOTER_PATTERNS:
        if pattern.match(stripped):
            return True

    normalized = _normalize_for_match(stripped)
    if normalized in TEMPLATE_ARTIFACT_LINES:
        return True

    if _metadata_token_count(stripped) >= 2:
        return True

    if _is_title_or_header_line(stripped, title):
        return True

    if normalized in _title_variants(title):
        return True

    artist_variants = _artist_variants(artist)
    if normalized in artist_variants:
        return True

    if " - " in stripped and any(marker in artist.lower() for marker in GENIUS_ARTIST_MARKERS):
        left, _, right = stripped.partition(" - ")
        if _normalize_for_match(left) in _title_variants(title):
            return True
        if _normalize_for_match(right) in artist_variants:
            return True

    if clean_artist(artist).lower() in GENIUS_ARTIST_MARKERS and normalized in {
        "translations",
        "translation",
    }:
        return True

    return False


def strip_inline_annotations(line: str) -> str:
    """Remove inline scrape artifacts: contributor prefixes, URLs, hashtags,
    emojis, music-note markers, embed markers, and video suffixes."""
    line = CONTRIBUTOR_PREFIX_RE.sub("", line)
    line = URL_RE.sub(" ", line)
    line = HASHTAG_RE.sub(" ", line)
    line = MUSIC_NOTE_RE.sub(" ", line)
    line = EMBED_SUFFIX_RE.sub("", line)
    line = TRAILING_VIDEO_RE.sub("", line)
    line = PAREN_ENGLISH_TRANSLATION_RE.sub("", line)
    line = EMOJI_RE.sub("", line)
    line = re.sub(r"\s+", " ", line).strip()
    return line


def normalize_quotes_in_line(line: str, strip_wrapping: bool = True) -> str:
    line = normalize_unicode(line)
    if strip_wrapping:
        line = line.strip("\"'")
    line = line.replace('""', '"').replace("''", "'")
    line = re.sub(r'"\s*([^"]+?)\s*"', r"\1", line)
    line = re.sub(r"'\s*([^']+?)\s*'", r"\1", line)
    return line.strip()


def collapse_blank_lines(lines: Iterable[str]) -> list[str]:
    cleaned: list[str] = []
    previous_blank = False
    for line in lines:
        if not line.strip():
            if not previous_blank:
                cleaned.append("")
            previous_blank = True
            continue
        cleaned.append(line)
        previous_blank = False
    while cleaned and not cleaned[0].strip():
        cleaned.pop(0)
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()
    return cleaned


def detect_script_style(text: str) -> str:
    has_dev = bool(DEVANAGARI_RE.search(text))
    has_roman = bool(ROMAN_RE.search(text))
    if has_dev and has_roman:
        return "mixed"
    if has_dev:
        return "devanagari"
    if has_roman:
        return "romanized"
    return "other"


def clean_lyrics_body(raw_lyrics: str, title: str, artist: str) -> tuple[str, list[str]]:
    """Return cleaned lyrics and a list of human-readable cleaning actions."""
    actions: list[str] = []
    kept_lines: list[str] = []

    for raw_line in (raw_lyrics or "").splitlines():
        if is_noise_line(raw_line, title, artist):
            actions.append(f"removed_noise:{raw_line.strip()[:80]}")
            continue

        line = normalize_quotes_in_line(raw_line)
        line = strip_inline_annotations(line)
        line = normalize_unicode(line)
        if not line:
            continue
        if is_noise_line(line, title, artist):
            actions.append(f"removed_inline:{line[:80]}")
            continue
        kept_lines.append(line)

    kept_lines = collapse_blank_lines(kept_lines)
    cleaned = "\n".join(kept_lines)
    return cleaned, actions
