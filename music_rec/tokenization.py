"""Devanagari tokenization and NFC normalization."""

from __future__ import annotations

import re
import unicodedata

_DEV_TOKEN_RE = re.compile(r"[\u0900-\u097F]+|[A-Za-z0-9]+")

_LEGACY_VOWEL_COMPOSITIONS = {
    "\u093E\u0947": "\u094B",  # ा + े -> ो
    "\u093E\u0948": "\u094C",  # ा + ै -> ौ
}

try:  # pragma: no cover - optional dependency
    from indicnlp.tokenize import indic_tokenize

    _HAS_INDIC = True
except Exception:  # pragma: no cover
    _HAS_INDIC = False


def normalize_nfc(text: str) -> str:
    """Normalize to NFC and compose legacy two-part Devanagari vowels."""
    normalized = unicodedata.normalize("NFC", text or "")
    for legacy, composed in _LEGACY_VOWEL_COMPOSITIONS.items():
        normalized = normalized.replace(legacy, composed)
    return normalized


def tokenize(text: str) -> list[str]:
    text = normalize_nfc(text)
    if not text.strip():
        return []
    if _HAS_INDIC:
        try:
            toks: list[str] = []
            for segment in text.split():
                toks.extend(indic_tokenize.trivial_tokenize(segment, lang="ne"))
            return [t for t in (tok.strip() for tok in toks) if t and not _is_punct(t)]
        except Exception:
            pass
    return _DEV_TOKEN_RE.findall(text)


def _is_punct(token: str) -> bool:
    return all(unicodedata.category(ch).startswith("P") or ch.isspace() for ch in token)


def token_count(text: str) -> int:
    return len(tokenize(text))


def indic_available() -> bool:
    return _HAS_INDIC
