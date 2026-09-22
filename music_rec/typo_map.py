"""Curated typo map for corpus spelling errors (index-time canonicalization).

The corpus is scraped, so some lines contain source typos (``अखै`` for
``आँखै``, ``हात्ने`` for ``हट्ने``) that no cleaner can recover. This module
loads a reviewed CSV of ``typo -> canonical`` mappings and applies them when
building the lexical index (and when rendering lyric lines), so search and
display use the intended spelling without re-embedding or retraining anything.

Map rows are token-level or phrase-level (space-separated token sequences,
longest match wins). Every entry is reviewed and reversible by editing
``eval/corpus_typo_map.csv``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import pandas as pd

_DEVANAGARI = "[\u0900-\u097F]"
_VALID_KINDS = {"token", "phrase"}


def _split_sequence(value: str) -> tuple[str, ...]:
    return tuple(part for part in str(value).split() if part)


@dataclass(frozen=True)
class TypoMap:
    tokens: dict[str, str] = field(default_factory=dict)
    phrases: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = ()

    @property
    def enabled(self) -> bool:
        return bool(self.tokens or self.phrases)

    def apply_phrases(self, tokens: Sequence[str]) -> list[str]:
        if not self.phrases:
            return list(tokens)
        by_first: dict[str, list[tuple[tuple[str, ...], tuple[str, ...]]]] = {}
        for typo, canonical in self.phrases:
            by_first.setdefault(typo[0], []).append((typo, canonical))
        for entries in by_first.values():
            entries.sort(key=lambda item: -len(item[0]))

        result: list[str] = []
        index = 0
        items = list(tokens)
        while index < len(items):
            token = items[index]
            replaced = False
            for typo, canonical in by_first.get(token, ()):
                end = index + len(typo)
                if tuple(items[index:end]) == typo:
                    result.extend(canonical)
                    index = end
                    replaced = True
                    break
            if replaced:
                continue
            result.append(token)
            index += 1
        return result

    def apply_tokens(self, tokens: Sequence[str]) -> list[str]:
        if not self.enabled:
            return list(tokens)
        return [
            self.tokens.get(token, token) for token in self.apply_phrases(tokens)
        ]

    def apply_text(self, text: str) -> str:
        if not self.enabled or not text:
            return text
        text_map: dict[str, str] = dict(self.tokens)
        for typo, canonical in self.phrases:
            text_map[" ".join(typo)] = " ".join(canonical)
        keys = sorted(text_map, key=len, reverse=True)
        pattern = re.compile(
            rf"(?<!{_DEVANAGARI})(?:{'|'.join(re.escape(key) for key in keys)})(?!{_DEVANAGARI})"
        )
        return pattern.sub(lambda match: text_map[match.group(0)], text)


def load_typo_map(path: Path | None, *, enabled: bool = True) -> TypoMap:
    if not enabled or path is None or not Path(path).exists():
        return TypoMap()
    frame = pd.read_csv(path, encoding="utf-8").fillna("")
    tokens: dict[str, str] = {}
    phrases: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
    for row in frame.itertuples(index=False):
        kind = str(getattr(row, "kind", "")).strip().lower()
        typo = str(getattr(row, "typo", "")).strip()
        canonical = str(getattr(row, "canonical", "")).strip()
        if kind not in _VALID_KINDS or not typo or not canonical or typo == canonical:
            continue
        if kind == "token":
            if " " in typo or " " in canonical:
                continue
            tokens[typo] = canonical
        else:
            typo_tokens = _split_sequence(typo)
            canonical_tokens = _split_sequence(canonical)
            if len(typo_tokens) < 2 or not canonical_tokens:
                continue
            phrases.append((typo_tokens, canonical_tokens))
    phrases.sort(key=lambda item: -len(item[0]))
    return TypoMap(tokens=tokens, phrases=tuple(phrases))
