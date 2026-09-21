"""Transliteration quality harness: line/word CER, exact-match, lexicon validity.

Evaluates the installed checkpoint against the committed gold sets
(``eval/translit_gold_lines.csv``, ``eval/translit_gold_words.csv``), checks the
English gate on inline cases, and measures how many Devanagari tokens produced
for real romanized corpus songs are attested words in the independently
Devanagari-written part of the corpus. Writes
``music_rec_artifacts/transliteration_report.json`` and exits nonzero when a
metric crosses its regression threshold.

Usage:
    python scripts/check_transliteration.py
    python scripts/check_transliteration.py --decode beam --limit 50
    python scripts/check_transliteration.py --no-lexicon
    python scripts/check_transliteration.py --max-line-cer 0.06 --min-line-exact 0.40
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import random
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.translit_metrics import error_rows, evaluate_pairs  # noqa: E402
from lyrics_pipeline.cleaner import clean_lyrics_body  # noqa: E402
from lyrics_pipeline.transliterator import NepaliTransliterator  # noqa: E402

GOLD_LINES = PROJECT_ROOT / "eval" / "translit_gold_lines.csv"
GOLD_WORDS = PROJECT_ROOT / "eval" / "translit_gold_words.csv"
CORPUS_CSV = PROJECT_ROOT / "CSVs Dataset" / "corpus_final_v2.csv"
CORPUS_RAW = PROJECT_ROOT / "R_data" / "corpus" / "corpus_raw.csv"
CHECKPOINT = PROJECT_ROOT / "new_char_transformer_best.pt"
DEFAULT_OUT = PROJECT_ROOT / "music_rec_artifacts" / "transliteration_report.json"

DEV_WORD_RE = re.compile(r"[\u0900-\u097F]+")
ROMAN_RE = re.compile(r"[A-Za-z]")

GATE_CASES = [
    {"input": "I love you baby", "kind": "unchanged"},
    {"input": "don't you know my name", "kind": "unchanged"},
    {"input": "timi lai maya garchu", "kind": "no_roman"},
    {"input": "I love you bhanne geet", "kind": "mixed"},
]


def load_gold_lines(limit: int = 0) -> list[dict]:
    with open(GOLD_LINES, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return rows[:limit] if limit else rows


def load_gold_words(limit: int = 0) -> list[dict]:
    with open(GOLD_WORDS, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return rows[:limit] if limit else rows


def checkpoint_info(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "found": False}
    info: dict = {"path": str(path), "found": True}
    try:
        import torch

        payload = torch.load(path, map_location="cpu", weights_only=False)
    except Exception as error:  # pragma: no cover - metadata only
        info["error"] = str(error)
        return info
    if isinstance(payload, dict):
        for key in ("phase_name", "epoch", "best_val_cer"):
            if key in payload:
                info[key] = payload[key]
        state = payload.get("model_state")
        if isinstance(state, dict):
            info["params"] = int(sum(value.numel() for value in state.values()))
    return info


def evaluate_lines(transliterator: NepaliTransliterator, rows: list[dict]) -> dict:
    pairs: list[tuple[str, str]] = []
    by_difficulty: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for row in rows:
        prediction = transliterator.transliterate_text(row["roman"])
        reference = row["devanagari"]
        pairs.append((prediction, reference))
        by_difficulty[row["difficulty"]].append((prediction, reference))
    report = evaluate_pairs(pairs)
    report["by_difficulty"] = {
        name: evaluate_pairs(group) for name, group in sorted(by_difficulty.items())
    }
    report["worst"] = error_rows(pairs, limit=10)
    return report


def evaluate_words(transliterator: NepaliTransliterator, rows: list[dict]) -> dict:
    romans = [row["roman"] for row in rows]
    predictions = transliterator.transliterate_tokens(romans)
    pairs = list(zip(predictions, (row["devanagari"] for row in rows)))
    report = evaluate_pairs(pairs)
    report["worst"] = error_rows(pairs, limit=10)
    return report


def evaluate_gate(transliterator: NepaliTransliterator) -> dict:
    cases = []
    for case in GATE_CASES:
        output = transliterator.transliterate_text(case["input"])
        kind = case["kind"]
        if kind == "unchanged":
            passed = output == case["input"]
        elif kind == "no_roman":
            passed = not ROMAN_RE.search(output)
        elif kind == "mixed":
            passed = "I love you" in output and "bhanne" not in output
        else:  # pragma: no cover - guarded by the table above
            raise ValueError(f"unknown gate case kind: {kind}")
        cases.append(
            {
                "input": case["input"],
                "kind": kind,
                "output": output,
                "passed": passed,
            }
        )
    return {
        "cases": cases,
        "passed": sum(1 for case in cases if case["passed"]),
        "total": len(cases),
    }


def evaluate_lexicon_validity(
    transliterator: NepaliTransliterator, n_songs: int, seed: int = 42
) -> dict | None:
    """Share of produced Devanagari tokens that are attested corpus words.

    The lexicon is built only from songs written in Devanagari originally, so it
    does not inherit the transliterator's own output. Songs with no lines are
    skipped; sampling is deterministic. This is a *lower bound*: valid words that
    simply never occur in the 1,421-song Devanagari reference set (e.g.
    ``खेलिरहेको``) count as misses, so treat it as a relative regression signal,
    not an absolute accuracy.
    """
    if not CORPUS_CSV.exists() or not CORPUS_RAW.exists():
        return None

    lexicon: Counter = Counter()
    lexicon_songs = 0
    with open(CORPUS_CSV, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("script_style_original") != "devanagari":
                continue
            lexicon_songs += 1
            lexicon.update(DEV_WORD_RE.findall(row.get("lyrics_devanagari") or ""))

    candidates = []
    with open(CORPUS_RAW, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("script") == "romanized":
                candidates.append(row)
    rng = random.Random(seed)
    sample = rng.sample(candidates, min(n_songs, len(candidates)))

    produced: Counter = Counter()
    for row in sample:
        text, _ = clean_lyrics_body(
            row.get("Lyrics") or "", row.get("Title") or "", row.get("Artist") or ""
        )
        if not text.strip():
            continue
        produced.update(DEV_WORD_RE.findall(transliterator.transliterate_text(text)))

    total = sum(produced.values())
    in_lexicon = sum(count for word, count in produced.items() if word in lexicon)
    missing = [(word, count) for word, count in produced.most_common() if word not in lexicon]
    return {
        "lexicon_songs": lexicon_songs,
        "lexicon_types": len(lexicon),
        "sampled_songs": len(sample),
        "output_tokens": total,
        "in_lexicon": in_lexicon,
        "in_lexicon_ratio": round(in_lexicon / total, 4) if total else 0.0,
        "top_out_of_lexicon": [{"word": word, "count": count} for word, count in missing[:20]],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decode", choices=["greedy", "beam"], default="greedy")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--limit", type=int, default=0, help="Only score the first N gold rows")
    parser.add_argument("--no-lexicon", action="store_true", help="Skip the lexicon-validity probe")
    parser.add_argument("--lexicon-songs", type=int, default=60)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--max-line-cer", type=float, default=0.115)
    parser.add_argument("--min-line-exact", type=float, default=0.08)
    parser.add_argument("--max-word-cer", type=float, default=0.18)
    parser.add_argument("--min-word-exact", type=float, default=0.50)
    parser.add_argument("--min-lexicon-ratio", type=float, default=0.82)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    transliterator = NepaliTransliterator(decode=args.decode, beam_size=args.beam_size)
    if not transliterator.available:
        print("transliterator checkpoint not available; nothing to score")
        return 2

    started = time.perf_counter()
    lines = evaluate_lines(transliterator, load_gold_lines(args.limit))
    words = evaluate_words(transliterator, load_gold_words(args.limit))
    gate = evaluate_gate(transliterator)
    lexicon = (
        None
        if args.no_lexicon
        else evaluate_lexicon_validity(transliterator, args.lexicon_songs)
    )

    thresholds = {
        "max_line_cer": args.max_line_cer,
        "min_line_exact": args.min_line_exact,
        "max_word_cer": args.max_word_cer,
        "min_word_exact": args.min_word_exact,
        "min_lexicon_ratio": args.min_lexicon_ratio,
    }
    checks = {
        "line_cer": lines["cer"] <= args.max_line_cer,
        "line_exact": lines["exact_match"] >= args.min_line_exact,
        "word_cer": words["cer"] <= args.max_word_cer,
        "word_exact": words["exact_match"] >= args.min_word_exact,
        "gate": gate["passed"] == gate["total"],
    }
    if lexicon is not None:
        checks["lexicon_ratio"] = lexicon["in_lexicon_ratio"] >= args.min_lexicon_ratio
    passed = all(checks.values())

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "checkpoint": checkpoint_info(CHECKPOINT),
        "config": {
            "decode": args.decode,
            "beam_size": args.beam_size,
            "limit": args.limit,
            "lexicon_songs": args.lexicon_songs,
        },
        "lines": lines,
        "words": words,
        "gate": gate,
        "lexicon_validity": lexicon,
        "thresholds": thresholds,
        "checks": checks,
        "passed": passed,
        "seconds": round(time.perf_counter() - started, 1),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    by_difficulty = " ".join(
        f"{name}={group['cer']:.3f}" for name, group in lines["by_difficulty"].items()
    )
    print(f"checkpoint: {CHECKPOINT.name} (phase={report['checkpoint'].get('phase_name')}, "
          f"best_val_cer={report['checkpoint'].get('best_val_cer')})")
    print(f"lines: n={lines['n']} cer={lines['cer']:.4f} exact={lines['exact_match']:.1%} ({by_difficulty})")
    print(f"words: n={words['n']} cer={words['cer']:.4f} exact={words['exact_match']:.1%}")
    print(f"gate:  {gate['passed']}/{gate['total']} cases pass")
    if lexicon is not None:
        print(
            f"lexicon: {lexicon['in_lexicon']}/{lexicon['output_tokens']} tokens "
            f"({lexicon['in_lexicon_ratio']:.1%}) in {lexicon['lexicon_types']} attested types "
            "(lower bound)"
        )
    failed = [name for name, ok in checks.items() if not ok]
    print(f"thresholds: {'PASS' if passed else 'FAIL ' + ', '.join(failed)}")
    print(f"report -> {args.out}  ({report['seconds']}s)")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
