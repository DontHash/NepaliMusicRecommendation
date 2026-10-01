"""Near-duplicate song detection for identity review (MinHash/LSH).

Folded artist+title strings rarely match exactly across catalogs
("Kali Prasad Baskota - Khusi" vs "kali prasad baskota - Khusi (Official
Video)"). This module builds MinHash signatures over word bigrams of the
folded ``artist title`` string, uses MinHashLSH for candidate generation, and
filters pairs with exact token Jaccard.

The output is a *review queue*, not an auto-merge: every pair carries a
suggested action and an empty ``decision`` column for a human/operator to fill.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from datasketch import MinHash, MinHashLSH

from .normalize import fold
from .prune import priority

NUM_PERM = 64
DEFAULT_THRESHOLD = 0.6
SCRIPT_RANK = {"devanagari": 0, "mixed": 1, "romanized": 2, "unknown": 3}

REVIEW_FIELDS = [
    "left_key", "right_key",
    "left_artist", "left_title", "left_source", "left_isrc",
    "right_artist", "right_title", "right_source", "right_isrc",
    "similarity", "suggested_action", "suggested_keep", "decision",
]


@dataclass(frozen=True)
class SongRecord:
    key: str
    artist: str
    title: str
    source: str = ""
    script: str = ""
    isrc: str = ""
    lyrics_sha256: str = ""

    @property
    def text(self) -> str:
        return f"{self.artist} {self.title}"


def _tokens(text: str) -> list[str]:
    words = fold(text).split()
    if len(words) < 2:
        return words
    return [" ".join(pair) for pair in zip(words, words[1:])] + words


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _signature(tokens: list[str], num_perm: int) -> MinHash:
    signature = MinHash(num_perm=num_perm)
    for token in tokens:
        signature.update(token.encode("utf-8"))
    return signature


def near_duplicate_pairs(records: list[SongRecord], *, threshold: float = DEFAULT_THRESHOLD,
                         num_perm: int = NUM_PERM) -> list[tuple[int, int, float]]:
    """Return (left_index, right_index, jaccard) pairs, best similarity first."""
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    token_sets: list[set[str]] = []
    signatures: list[MinHash] = []
    for index, record in enumerate(records):
        tokens = _tokens(record.text)
        token_sets.append(set(tokens))
        signatures.append(_signature(tokens, num_perm))
        lsh.insert(str(index), signatures[-1])

    pairs: list[tuple[int, int, float]] = []
    for index in range(len(records)):
        for candidate in lsh.query(signatures[index]):
            other = int(candidate)
            if other <= index:
                continue
            similarity = _jaccard(token_sets[index], token_sets[other])
            if similarity >= threshold:
                pairs.append((index, other, round(similarity, 4)))
    pairs.sort(key=lambda pair: (-pair[2], pair[0], pair[1]))
    return pairs


def _rank(record: SongRecord) -> tuple[int, int]:
    return (priority(record.source), SCRIPT_RANK.get(record.script, 3))


def suggest_action(left: SongRecord, right: SongRecord) -> tuple[str, str]:
    """Suggest (action, keep_side); survivorship prefers source priority then script."""
    same_artist = fold(left.artist) == fold(right.artist)
    same_title = fold(left.title) == fold(right.title)
    if same_artist and same_title:
        action = "merge_candidate"
    elif same_artist:
        action = "review_title_variant"
    else:
        action = "review"
    keep_side = "left" if _rank(left) <= _rank(right) else "right"
    return action, keep_side


def review_songs(records: list[SongRecord], *, threshold: float = DEFAULT_THRESHOLD,
                 num_perm: int = NUM_PERM) -> list[dict]:
    rows: list[dict] = []
    for left_index, right_index, similarity in near_duplicate_pairs(
            records, threshold=threshold, num_perm=num_perm):
        left, right = records[left_index], records[right_index]
        action, keep_side = suggest_action(left, right)
        rows.append({
            "left_key": left.key, "right_key": right.key,
            "left_artist": left.artist, "left_title": left.title,
            "left_source": left.source, "left_isrc": left.isrc,
            "right_artist": right.artist, "right_title": right.title,
            "right_source": right.source, "right_isrc": right.isrc,
            "similarity": similarity, "suggested_action": action,
            "suggested_keep": keep_side, "decision": "pending",
        })
    return rows


def load_corpus_records(path: Path | str) -> list[SongRecord]:
    """Read a compacted corpus CSV (corpus_raw.csv) into SongRecords."""
    records: list[SongRecord] = []
    with open(path, "r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            artist = row.get("Artist", "") or ""
            title = row.get("Title", "") or ""
            records.append(SongRecord(
                key=row.get("sha256") or f"{fold(artist)}|{fold(title)}",
                artist=artist, title=title,
                source=row.get("source", "") or "",
                script=row.get("script", "") or "",
                isrc=row.get("isrc", "") or "",
                lyrics_sha256=row.get("sha256", "") or "",
            ))
    return records


def write_review(rows: list[dict], output: Path | str) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, output)


def review_file(input_path: Path | str, output_path: Path | str, *,
                threshold: float = DEFAULT_THRESHOLD, num_perm: int = NUM_PERM) -> dict:
    input_path, output_path = Path(input_path), Path(output_path)
    records = load_corpus_records(input_path)
    rows = review_songs(records, threshold=threshold, num_perm=num_perm)
    write_review(rows, output_path)
    return {
        "input": str(input_path),
        "input_sha256": hashlib.sha256(input_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "output": str(output_path),
        "threshold": threshold,
        "records": len(records),
        "pairs": len(rows),
        "merge_candidates": sum(1 for row in rows if row["suggested_action"] == "merge_candidate"),
        "pending_decisions": sum(1 for row in rows if row["decision"] == "pending"),
    }


def write_report(report: dict, path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
