"""Teacher sanity check for transliteration: Gemini labels vs the human gold.

Measures line CER and exact-match for the teacher and for the installed
checkpoint on the same gold rows, plus their agreement with each other. This is
the A1 gate: if the teacher does not clearly beat the model on in-domain lines,
teacher-distilled training data is not worth producing.

Usage:
    python eval/translit_teacher_eval.py
    python eval/translit_teacher_eval.py --max-cer 0.05
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.translit_metrics import error_rows, evaluate_pairs  # noqa: E402
from lyrics_pipeline.transliterator import NepaliTransliterator  # noqa: E402

GOLD_LINES = PROJECT_ROOT / "eval" / "translit_gold_lines.csv"
DEFAULT_LABELS = PROJECT_ROOT / "R_data" / "raw" / "gemini" / "translit_gold_v1" / "labels.csv"
DEFAULT_OUT = PROJECT_ROOT / "music_rec_artifacts" / "translit_teacher_report.json"

PAREN_RE = re.compile(r"[\(\)\[\]—–]")


def normalized(text: str) -> str:
    """Formatting-insensitive form: no parentheticals/dashes, single spaces.

    Separates transliteration quality from fidelity drift (dropped repeats,
    token merges) so the teacher's orthography can be judged on its own.
    """
    return re.sub(r"\s+", " ", PAREN_RE.sub(" ", text)).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--max-cer", type=float, default=0.05)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.labels.exists():
        sys.exit(f"teacher labels not found: {args.labels}")

    with open(GOLD_LINES, encoding="utf-8", newline="") as handle:
        gold_rows = list(csv.DictReader(handle))
    with open(args.labels, encoding="utf-8", newline="") as handle:
        teacher = {row["line_id"]: row["devanagari"] for row in csv.DictReader(handle)}

    missing = [row["line_id"] for row in gold_rows if row["line_id"] not in teacher]
    if missing:
        sys.exit(f"teacher labels incomplete: {len(missing)} missing (e.g. {missing[:3]})")

    transliterator = NepaliTransliterator()
    if not transliterator.available:
        sys.exit("transliterator checkpoint not available")

    teacher_pairs: list[tuple[str, str]] = []
    model_pairs: list[tuple[str, str]] = []
    agreement_pairs: list[tuple[str, str]] = []
    teacher_norm_pairs: list[tuple[str, str]] = []
    model_norm_pairs: list[tuple[str, str]] = []
    by_difficulty: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for row in gold_rows:
        reference = row["devanagari"]
        teacher_prediction = teacher[row["line_id"]]
        model_prediction = transliterator.transliterate_text(row["roman"])
        teacher_pairs.append((teacher_prediction, reference))
        model_pairs.append((model_prediction, reference))
        teacher_norm_pairs.append((normalized(teacher_prediction), normalized(reference)))
        model_norm_pairs.append((normalized(model_prediction), normalized(reference)))
        agreement_pairs.append((teacher_prediction, model_prediction))
        by_difficulty[row["difficulty"]].append((teacher_prediction, reference))

    teacher_report = evaluate_pairs(teacher_pairs)
    model_report = evaluate_pairs(model_pairs)
    agreement = evaluate_pairs(agreement_pairs)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "labels": str(args.labels),
        "n": teacher_report["n"],
        "teacher": teacher_report,
        "model": model_report,
        "teacher_normalized": evaluate_pairs(teacher_norm_pairs),
        "model_normalized": evaluate_pairs(model_norm_pairs),
        "teacher_vs_model_agreement": agreement,
        "teacher_by_difficulty": {
            name: evaluate_pairs(group) for name, group in sorted(by_difficulty.items())
        },
        "teacher_worst": error_rows(teacher_pairs, limit=10),
        "model_worst": error_rows(model_pairs, limit=10),
        "max_cer": args.max_cer,
        "passed": teacher_report["cer"] < args.max_cer and teacher_report["cer"] < model_report["cer"],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"n={teacher_report['n']} lines")
    print(
        f"teacher: cer={teacher_report['cer']:.4f} exact={teacher_report['exact_match']:.1%}  "
        f"model: cer={model_report['cer']:.4f} exact={model_report['exact_match']:.1%}"
    )
    print(
        f"normalized (formatting-insensitive): "
        f"teacher={report['teacher_normalized']['cer']:.4f} model={report['model_normalized']['cer']:.4f}"
    )
    print(
        "teacher by difficulty: "
        + " ".join(
            f"{name}={group['cer']:.3f}" for name, group in report["teacher_by_difficulty"].items()
        )
    )
    print(
        f"teacher vs model agreement: exact={agreement['exact_match']:.1%} cer={agreement['cer']:.4f}"
    )
    print("teacher worst:")
    for row in report["teacher_worst"][:5]:
        print(f"  cer={row['cer']:.2f} pred={row['prediction']}  gold={row['reference']}")
    print(f"gate (teacher cer < {args.max_cer} and < model): {'PASS' if report['passed'] else 'FAIL'}")
    print(f"report -> {args.out}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
