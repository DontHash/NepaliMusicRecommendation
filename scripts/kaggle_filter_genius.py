"""Push/wait/pull the Kaggle Genius-Nepali filter job.

Usage:
    python scripts/kaggle_filter_genius.py push
    python scripts/kaggle_filter_genius.py status
    python scripts/kaggle_filter_genius.py wait
    python scripts/kaggle_filter_genius.py pull
    python scripts/kaggle_filter_genius.py run     # push + wait + pull
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import kaggle_transliterator as kt  # noqa: E402

DATASET_SOURCE = "carlosgdcj/genius-song-lyrics-with-language-information"
KERNEL_SLUG = "genius-nepali-filter"
KERNEL_TITLE = "Genius Nepali Filter"
KERNEL_SCRIPT = Path(__file__).resolve().parent / "kaggle_jobs" / "genius_filter.py"
DEFAULT_DEST = PROJECT_ROOT / "R_data" / "raw" / "kaggle"
DONE_STATUSES = {"complete", "error", "cancelled"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("push", "wait", "run"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--user", type=str, default=None)
        if name in {"wait", "run"}:
            cmd.add_argument("--kernel", type=str, default=None)
            cmd.add_argument("--interval", type=int, default=30)
            cmd.add_argument("--timeout", type=int, default=5400)
    status = sub.add_parser("status")
    status.add_argument("--kernel", type=str, default=None)
    pull = sub.add_parser("pull")
    pull.add_argument("--kernel", type=str, default=None)
    pull.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    return parser.parse_args()


def kernel_id(explicit: str | None = None, user: str | None = None) -> str:
    if explicit:
        return explicit
    return f"{kt.detect_username(user)}/{KERNEL_SLUG}"


def push_kernel(user: str | None) -> str:
    kt.require_kaggle()
    username = kt.detect_username(user)
    metadata = {
        "id": f"{username}/{KERNEL_SLUG}",
        "title": KERNEL_TITLE,
        "code_file": "genius_filter.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": False,
        "enable_internet": False,
        "competition_sources": [],
        "dataset_sources": [DATASET_SOURCE],
        "kernel_sources": [],
    }
    with tempfile.TemporaryDirectory(prefix="kaggle_genius_") as tmp:
        staging = Path(tmp)
        (staging / "genius_filter.py").write_text(KERNEL_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
        (staging / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        pushed = subprocess.run(
            ["kaggle", "kernels", "push", "-p", str(staging)],
            capture_output=True,
            text=True,
        )
        if pushed.returncode != 0:
            print(pushed.stdout)
            print(pushed.stderr)
            sys.exit(1)
        print(pushed.stdout.strip())
    return f"{username}/{KERNEL_SLUG}"


def kernel_status(kernel: str) -> str:
    result = subprocess.run(["kaggle", "kernels", "status", kernel], capture_output=True, text=True)
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


def pull_output(kernel: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(["kaggle", "kernels", "output", kernel, "-p", str(dest)], check=True)
    for name in ("genius_ne.csv", "filter_report.json"):
        path = dest / name
        print(f"{name}: {'ok' if path.exists() else 'MISSING'} ({path.stat().st_size if path.exists() else 0} bytes)")


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
        pull_output(kernel_id(args.kernel), args.dest)
    elif args.command == "run":
        kernel = push_kernel(args.user)
        print(f"kernel: https://www.kaggle.com/code/{kernel}")
        status = wait_for_completion(kernel, args.interval, args.timeout)
        if status != "complete":
            sys.exit(f"kernel finished with status: {status}")
        pull_output(kernel, DEFAULT_DEST)


if __name__ == "__main__":
    main()
