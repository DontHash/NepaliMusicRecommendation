"""Push/wait/pull the Kaggle sentiment-distillation job.

Usage:
    python scripts/kaggle_sentiment.py push
    python scripts/kaggle_sentiment.py status
    python scripts/kaggle_sentiment.py wait [--timeout 14400]
    python scripts/kaggle_sentiment.py pull
    python scripts/kaggle_sentiment.py run
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import kaggle_transliterator as kt  # noqa: E402

DATASET_SLUG = "projectr-cleaned-lyrics"
KERNEL_SLUG = "projectr-sentiment-distill"
KERNEL_TITLE = "ProjectR Sentiment Distill"
KERNEL_SCRIPT = Path(__file__).resolve().parent / "kaggle_jobs" / "sentiment_distill.py"
CLEANED_CSV = PROJECT_ROOT / "music_rec_artifacts" / "cleaned_lyrics.csv"
DEFAULT_DEST = PROJECT_ROOT / "R_data" / "raw" / "kaggle" / "sentiment_distill"
ARTIFACTS_DIR = PROJECT_ROOT / "music_rec_artifacts"
DONE_STATUSES = {"complete", "error", "cancelled"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("push", "wait", "run"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--user", type=str, default=None)
        if name in {"wait", "run"}:
            cmd.add_argument("--kernel", type=str, default=None)
            cmd.add_argument("--interval", type=int, default=60)
            cmd.add_argument("--timeout", type=int, default=14400)
    status = sub.add_parser("status")
    status.add_argument("--kernel", type=str, default=None)
    pull = sub.add_parser("pull")
    pull.add_argument("--kernel", type=str, default=None)
    pull.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    pull.add_argument("--no-install", action="store_true")
    return parser.parse_args()


def kernel_id(explicit: str | None = None, user: str | None = None) -> str:
    if explicit:
        return explicit
    return f"{kt.detect_username(user)}/{KERNEL_SLUG}"


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def push_kernel(user: str | None) -> str:
    kt.require_kaggle()
    username = kt.detect_username(user)
    dataset = f"{username}/{DATASET_SLUG}"
    metadata = {
        "id": f"{username}/{KERNEL_SLUG}",
        "title": KERNEL_TITLE,
        "code_file": "sentiment_distill.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": True,
        "competition_sources": [],
        "dataset_sources": [dataset],
        "kernel_sources": [],
    }
    with tempfile.TemporaryDirectory(prefix="kaggle_sentiment_") as tmp:
        staging = Path(tmp)
        (staging / "sentiment_distill.py").write_text(
            KERNEL_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8"
        )
        (staging / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        pushed = _run(["kaggle", "kernels", "push", "-p", str(staging)])
        if pushed.returncode != 0:
            print(pushed.stdout)
            print(pushed.stderr)
            sys.exit(1)
        print((pushed.stdout or pushed.stderr).strip())
    return f"{username}/{KERNEL_SLUG}"


def kernel_status(kernel: str) -> str:
    result = _run(["kaggle", "kernels", "status", kernel])
    output = (result.stdout or "") + (result.stderr or "")
    match = re.search(r'status["\s:]+([A-Za-z_.]+)', output)
    if match:
        return match.group(1).split(".")[-1].strip('."').lower()
    return output.strip()


def wait_for_completion(kernel: str, interval: int, timeout: int) -> str:
    start = time.time()
    last = ""
    while True:
        status = kernel_status(kernel)
        if status != last:
            print(f"[{time.strftime('%H:%M:%S')}] status: {status}")
            last = status
        if status in DONE_STATUSES:
            return status
        if time.time() - start > timeout:
            print(f"timeout after {timeout}s, last status: {status}")
            return status
        time.sleep(interval)


def install_scores(dest: Path) -> None:
    import numpy as np
    import pandas as pd

    scores_path = dest / "sentiment_scores_v2.csv"
    if not scores_path.exists():
        sys.exit(f"missing sentiment_scores_v2.csv in {dest}")
    scores = pd.read_csv(scores_path)
    expected = pd.read_csv(CLEANED_CSV, usecols=["song_id"])["song_id"].astype(int).tolist()
    if sorted(int(x) for x in scores["song_id"]) != sorted(expected):
        sys.exit("sentiment_scores_v2.csv song_ids do not match cleaned_lyrics.csv")
    if not np.isfinite(scores["sentiment_score"].to_numpy()).all():
        sys.exit("sentiment scores contain non-finite values")

    report_path = dest / "sentiment_distill_report.json"
    if report_path.exists():
        print(report_path.read_text(encoding="utf-8"))
    scores.to_csv(ARTIFACTS_DIR / "sentiment_scores.csv", index=False, encoding="utf-8")
    print(f"[install] sentiment_scores.csv ({len(scores)} songs, {len(scores.columns)} cols) -> {ARTIFACTS_DIR}")


def pull_output(kernel: str, dest: Path, install: bool = True) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(["kaggle", "kernels", "output", kernel, "-p", str(dest)], check=True)
    for name in ("sentiment_scores_v2.csv", "mood_pseudo_labels.csv", "sentiment_distill_report.json"):
        path = dest / name
        print(f"{name}: {'ok' if path.exists() else 'MISSING'} ({path.stat().st_size if path.exists() else 0} bytes)")
    if install:
        install_scores(dest)


def main() -> None:
    args = parse_args()
    if args.command == "push":
        kernel = push_kernel(args.user)
        print(f"kernel: https://www.kaggle.com/code/{kernel}")
    elif args.command == "status":
        print(kernel_status(kernel_id(args.kernel)))
    elif args.command == "wait":
        kernel = kernel_id(args.kernel)
        print(wait_for_completion(kernel, args.interval, args.timeout))
    elif args.command == "pull":
        pull_output(kernel_id(args.kernel), args.dest, install=not args.no_install)
    elif args.command == "run":
        kernel = push_kernel(args.user)
        print(f"kernel: https://www.kaggle.com/code/{kernel}")
        status = wait_for_completion(kernel, args.interval, args.timeout)
        if status != "complete":
            sys.exit(f"kernel finished with status: {status}")
        pull_output(kernel, DEFAULT_DEST)


if __name__ == "__main__":
    main()
