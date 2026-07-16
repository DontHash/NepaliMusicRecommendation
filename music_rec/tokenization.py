"""Devanagari tokenization and NFC normalization."""

from __future__ import annotations

import re
import unicodedata

_DEV_TOKEN_RE = re.compile(r"[\u0900-\u097F]+|[A-Za-z0-9]+")

try:  # pragma: no cover - optional dependency
    from indicnlp.tokenize import indic_tokenize

    _HAS_INDIC = True
except Exception:  # pragma: no cover
    _HAS_INDIC = False


def normalize_nfc(text: str) -> str:
    """Normalize to NFC (canonical composed form) for consistent Devanagari."""
    return unicodedata.normalize("NFC", text or "")


def tokenize(text: str) -> list[str]:
    text = normalize_nfc(text)
    if not text.strip():
        return []
    if _HAS_INDIC:
        try:
            toks = indic_tokenize.trivial_tokenize(text, lang="ne")
            return [t for t in toks if t.strip() and not _is_punct(t)]
        except Exception:
            pass
    return _DEV_TOKEN_RE.findall(text)


def _is_punct(token: str) -> bool:
    return all(unicodedata.category(ch).startswith("P") or ch.isspace() for ch in token)


def token_count(text: str) -> int:
    return len(tokenize(text))


def indic_available() -> bool:
    return _HAS_INDIC
