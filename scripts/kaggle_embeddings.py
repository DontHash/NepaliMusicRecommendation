"""Push/wait/pull the Kaggle chunked lyric-embeddings job.

Usage:
    python scripts/kaggle_embeddings.py push
    python scripts/kaggle_embeddings.py status
    python scripts/kaggle_embeddings.py wait
    python scripts/kaggle_embeddings.py pull
    python scripts/kaggle_embeddings.py run     # push + wait + pull
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
DATASET_TITLE = "ProjectR Cleaned Lyrics"
KERNEL_SLUG = "projectr-lyric-embeddings-chunked"
KERNEL_TITLE = "ProjectR Lyric Embeddings Chunked"
KERNEL_SCRIPT = Path(__file__).resolve().parent / "kaggle_jobs" / "lyric_embeddings.py"
CLEANED_CSV = PROJECT_ROOT / "music_rec_artifacts" / "cleaned_lyrics.csv"
DEFAULT_DEST = PROJECT_ROOT / "R_data" / "raw" / "kaggle" / "lyric_embeddings"
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
            cmd.add_argument("--interval", type=int, default=30)
            cmd.add_argument("--timeout", type=int, default=5400)
    status = sub.add_parser("status")
    status.add_argument("--kernel", type=str, default=None)
    pull = sub.add_parser("pull")
    pull.add_argument("--kernel", type=str, default=None)
    pull.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    pull.add_argument("--no-install", action="store_true", help="Download only; skip validation/copy into artifacts")
    return parser.parse_args()


def kernel_id(explicit: str | None = None, user: str | None = None) -> str:
    if explicit:
        return explicit
    return f"{kt.detect_username(user)}/{KERNEL_SLUG}"


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def wait_dataset_ready(dataset: str, interval: int = 15, timeout: int = 600) -> None:
    start = time.time()
    while time.time() - start < timeout:
        result = _run(["kaggle", "datasets", "status", dataset])
        output = (result.stdout or "") + (result.stderr or "")
        lowered = output.lower()
        if "ready" in lowered:
            print(f"dataset ready: {dataset}")
            return
        if "error" in lowered or "failed" in lowered:
            sys.exit(f"dataset processing failed:\n{output.strip()}")
        time.sleep(interval)
    sys.exit(f"dataset not ready after {timeout}s:\n{output.strip()}")


def push_dataset(user: str | None) -> str:
    kt.require_kaggle()
    if not CLEANED_CSV.exists():
        sys.exit(f"missing {CLEANED_CSV}")
    username = kt.detect_username(user)
    dataset = f"{username}/{DATASET_SLUG}"
    rows = sum(1 for _ in CLEANED_CSV.open(encoding="utf-8")) - 1
    with tempfile.TemporaryDirectory(prefix="kaggle_ds_") as tmp:
        staging = Path(tmp)
        shutil.copy2(CLEANED_CSV, staging / "cleaned_lyrics.csv")
        metadata = {"title": DATASET_TITLE, "id": dataset, "licenses": [{"name": "other"}]}
        (staging / "dataset-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        created = _run(["kaggle", "datasets", "create", "-p", str(staging)])
        if created.returncode != 0:
            versioned = _run(
                ["kaggle", "datasets", "version", "-p", str(staging), "-m", f"cleaned lyrics ({rows} songs)"]
            )
            if versioned.returncode != 0:
                print(created.stdout, created.stderr)
                print(versioned.stdout, versioned.stderr)
                sys.exit("dataset create/version failed")
            print(versioned.stdout.strip() or versioned.stderr.strip())
        else:
            print(created.stdout.strip() or created.stderr.strip())
    wait_dataset_ready(dataset)
    return dataset


def push_kernel(user: str | None, dataset: str) -> str:
    kt.require_kaggle()
    username = kt.detect_username(user)
    metadata = {
        "id": f"{username}/{KERNEL_SLUG}",
        "title": KERNEL_TITLE,
        "code_file": "lyric_embeddings.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": True,
        "competition_sources": [],
        "dataset_sources": [dataset],
        "kernel_sources": [],
    }
    with tempfile.TemporaryDirectory(prefix="kaggle_kernel_") as tmp:
        staging = Path(tmp)
        (staging / "lyric_embeddings.py").write_text(
            KERNEL_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8"
        )
        (staging / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        pushed = _run(["kaggle", "kernels", "push", "-p", str(staging)])
        if pushed.returncode != 0:
            print(pushed.stdout)
            print(pushed.stderr)
            sys.exit(1)
        print(pushed.stdout.strip() or pushed.stderr.strip())
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


def install_artifacts(dest: Path) -> None:
    import numpy as np
    import pandas as pd

    emb_path = dest / "embeddings.npy"
    ids_path = dest / "embedding_ids.json"
    report_path = dest / "embed_report.json"
    if not emb_path.exists() or not ids_path.exists():
        sys.exit(f"missing embeddings.npy / embedding_ids.json in {dest}")
    if report_path.exists():
        print(report_path.read_text(encoding="utf-8"))

    matrix = np.load(emb_path)
    ids = [int(x) for x in json.loads(ids_path.read_text(encoding="utf-8"))]
    expected = [int(x) for x in pd.read_csv(CLEANED_CSV, usecols=["song_id"])["song_id"].tolist()]
    if matrix.shape[0] != len(expected):
        sys.exit(f"row mismatch: embeddings {matrix.shape[0]} vs cleaned_lyrics {len(expected)}")
    if ids != expected:
        sys.exit("embedding_ids.json order does not match cleaned_lyrics.csv song_id order")
    if not np.isfinite(matrix).all():
        sys.exit("embeddings contain non-finite values")

    shutil.copy2(emb_path, ARTIFACTS_DIR / "embeddings.npy")
    shutil.copy2(ids_path, ARTIFACTS_DIR / "embedding_ids.json")
    print(f"[install] embeddings.npy {matrix.shape} + embedding_ids.json ({len(ids)} ids) -> {ARTIFACTS_DIR}")


def pull_output(kernel: str, dest: Path, install: bool = True) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(["kaggle", "kernels", "output", kernel, "-p", str(dest)], check=True)
    for name in ("embeddings.npy", "embedding_ids.json", "embed_report.json"):
        path = dest / name
        print(f"{name}: {'ok' if path.exists() else 'MISSING'} ({path.stat().st_size if path.exists() else 0} bytes)")
    if install:
        install_artifacts(dest)


def main() -> None:
    args = parse_args()
    if args.command == "push":
        dataset = push_dataset(args.user)
        kernel = push_kernel(args.user, dataset)
        print(f"dataset: https://www.kaggle.com/datasets/{dataset}")
        print(f"kernel: https://www.kaggle.com/code/{kernel}")
    elif args.command == "status":
        print(kernel_status(kernel_id(args.kernel)))
    elif args.command == "wait":
        kernel = kernel_id(args.kernel)
        print(wait_for_completion(kernel, args.interval, args.timeout))
    elif args.command == "pull":
        pull_output(kernel_id(args.kernel), args.dest, install=not args.no_install)
    elif args.command == "run":
        dataset = push_dataset(args.user)
        kernel = push_kernel(args.user, dataset)
        print(f"kernel: https://www.kaggle.com/code/{kernel}")
        status = wait_for_completion(kernel, args.interval, args.timeout)
        if status != "complete":
            sys.exit(f"kernel finished with status: {status}")
        pull_output(kernel, DEFAULT_DEST)


if __name__ == "__main__":
    main()
