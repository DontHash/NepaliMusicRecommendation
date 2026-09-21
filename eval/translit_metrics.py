"""Transliteration metrics: character error rate and exact-match."""

from __future__ import annotations


def levenshtein(left: str, right: str) -> int:
    """Character edit distance (substitutions, insertions, deletions)."""
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            current.append(
                min(
                    current[j - 1] + 1,
                    previous[j] + 1,
                    previous[j - 1] + (left_char != right_char),
                )
            )
        previous = current
    return previous[-1]


def evaluate_pairs(pairs: list[tuple[str, str]]) -> dict:
    """Micro-averaged CER and exact-match over (prediction, reference) pairs."""
    distance = 0
    reference_chars = 0
    exact = 0
    for prediction, reference in pairs:
        distance += levenshtein(prediction, reference)
        reference_chars += max(len(reference), 1)
        exact += int(prediction == reference)
    total = len(pairs)
    return {
        "n": total,
        "cer": round(distance / reference_chars, 4) if reference_chars else 0.0,
        "exact_match": round(exact / total, 4) if total else 0.0,
        "exact": exact,
        "distance": distance,
        "reference_chars": reference_chars,
    }


def error_rows(pairs: list[tuple[str, str]], limit: int = 10) -> list[dict]:
    """Worst mismatching pairs by CER, for the report samples."""
    rows = []
    for prediction, reference in pairs:
        if prediction == reference:
            continue
        distance = levenshtein(prediction, reference)
        rows.append(
            {
                "prediction": prediction,
                "reference": reference,
                "distance": distance,
                "cer": round(distance / max(len(reference), 1), 4),
            }
        )
    rows.sort(key=lambda row: (-row["cer"], -row["distance"]))
    return rows[:limit]
