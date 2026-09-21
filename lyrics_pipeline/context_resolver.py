"""Line-level context resolution for ambiguous roman tokens.

The lexicon covers unambiguous words; the tokens left over (``ma``, ``ra``,
``na``, ``ki``, ...) are exactly the ones the word-level model gets wrong,
because their reading depends on the sentence. This resolver runs a
left-to-right pass over a transliterated line and picks, for each ambiguous
token, the attested reading that best fits the previous word, blending the
teacher-mined bigram table with the reading prior.
"""

from __future__ import annotations

import math

from .translit_context import BIGRAM, FORWARD_BIGRAM, READINGS

BIGRAM_WEIGHT = 0.75
LEFT_WEIGHT = 1.0
RIGHT_WEIGHT = 0.6


def candidate_readings(roman: str) -> tuple[str, ...]:
    readings = READINGS.get(roman)
    if not readings:
        return ()
    return tuple(readings)


def _prior(roman: str, candidate: str) -> float:
    readings = READINGS.get(roman) or {}
    total = sum(readings.values()) or 1
    return (readings.get(candidate, 0) + 0.5) / (total + 0.5 * max(len(readings), 1))


def _blend(table: dict[str, dict[str, int]], candidate: str, neighbour: str, prior: float) -> float:
    counts = table.get(candidate)
    if not counts:
        return prior
    total = sum(counts.values()) or 1
    seen = counts.get(neighbour, 0)
    if not seen:
        return prior
    conditional = (seen + 0.1) / (total + 0.1 * len(counts))
    return BIGRAM_WEIGHT * conditional + (1 - BIGRAM_WEIGHT) * prior


def _score(
    roman: str, candidate: str, previous: str | None, following: str | None
) -> float:
    """Weighted log-score from whichever neighbours have evidence.

    The reading prior is used only when neither side has a bigram entry, so it
    cannot swamp real context; the left (previous) word carries more weight than
    the right one because postpositions follow their host noun in Nepali.
    """
    prior = _prior(roman, candidate)
    total = 0.0
    weight = 0.0
    if previous is not None and BIGRAM.get(candidate, {}).get(previous):
        total += LEFT_WEIGHT * math.log(_blend(BIGRAM, candidate, previous, prior))
        weight += LEFT_WEIGHT
    if following is not None and FORWARD_BIGRAM.get(candidate, {}).get(following):
        total += RIGHT_WEIGHT * math.log(
            _blend(FORWARD_BIGRAM, candidate, following, prior)
        )
        weight += RIGHT_WEIGHT
    if not weight:
        return math.log(prior)
    return total / weight


def resolve(tokens: list[str], romans: list[str | None]) -> list[str]:
    """Resolve ambiguous tokens using the neighbouring output tokens.

    ``tokens`` are the current outputs and ``romans`` the roman key per position
    (``None`` for fixed tokens such as punctuation or non-ambiguous words).
    Returns a new list; positions without candidates are left untouched.

    The reading prior is used as the fallback when neither neighbour has bigram
    evidence: an evidence gate was tried and scored worse on the line gold, so
    the resolver deliberately overrides on the majority reading instead.
    """
    resolved = list(tokens)
    for index, roman in enumerate(romans):
        if roman is None:
            continue
        options = candidate_readings(roman)
        if len(options) < 2:
            continue
        previous = resolved[index - 1] if index > 0 else "<s>"
        following = resolved[index + 1] if index + 1 < len(resolved) else "</s>"
        resolved[index] = max(
            options, key=lambda option: _score(roman, option, previous, following)
        )
    return resolved
