"""Push the transliteration training notebook to Kaggle and pull the trained
model files back.

Prerequisites (once):
    pip install kaggle
    kaggle.com -> Settings -> Create New API Token -> save as ~/.kaggle/kaggle.json

Usage:
    python scripts/kaggle_transliterator.py push [--user YOUR_USERNAME]
    python scripts/kaggle_transliterator.py pull [--kernel USERNAME/newtransliterate]
    python scripts/kaggle_transliterator.py resume [--user YOUR_USERNAME]

`push` uploads and runs the training notebook (Aksharantar Nepali data is
downloaded automatically from Hugging Face). `pull` downloads the trained
checkpoint + vocab into the project root. `resume` picks up where a previous
run left off: it pulls the last checkpoint, publishes it as a small private
dataset, and re-pushes the notebook configured to attach it — the notebook's
built-in checkpoint resume logic then continues training from the saved epoch.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_NOTEBOOK = PROJECT_ROOT / "R_data" / "Notebooks" / "NewTransliterate.ipynb"
KERNEL_SLUG = "newtransliterate"
KERNEL_TITLE = "NewTransliterate"
RESUME_DATASET_SLUG = "translit-resume"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Kaggle helper for the transliterator model.")
    sub = parser.add_subparsers(dest="command", required=True)

    push = sub.add_parser("push", help="Push the training notebook to Kaggle")
    push.add_argument("--notebook", type=Path, default=DEFAULT_NOTEBOOK)
    push.add_argument("--user", type=str, default=None, help="Kaggle username (auto-detected if omitted)")
    push.add_argument(
        "--accelerator",
        choices=["t4", "auto"],
        default="t4",
        help="GPU shape: 't4' requests GPU T4 x2, 'auto' lets Kaggle pick (default: t4)",
    )

    pull = sub.add_parser("pull", help="Download trained checkpoint + vocab from Kaggle")
    pull.add_argument("--kernel", type=str, default=None, help="Kaggle kernel id (USERNAME/slug)")
    pull.add_argument("--dest", type=Path, default=PROJECT_ROOT)

    resume = sub.add_parser("resume", help="Resume training from the last checkpoint")
    resume.add_argument("--user", type=str, default=None, help="Kaggle username (auto-detected if omitted)")
    resume.add_argument("--kernel", type=str, default=None, help="Kaggle kernel id (USERNAME/slug)")
    resume.add_argument(
        "--checkpoint",
        type=Path,
        default=None,
        help="Local checkpoint to resume from (default: pull the last kernel output)",
    )
    resume.add_argument(
        "--accelerator",
        choices=["t4", "auto"],
        default="t4",
        help="GPU shape: 't4' requests GPU T4 x2, 'auto' lets Kaggle pick (default: t4)",
    )

    return parser.parse_args()


def kaggle_available() -> bool:
    return shutil.which("kaggle") is not None


def require_kaggle() -> None:
    if kaggle_available():
        return
    print(
        "The 'kaggle' command was not found.\n"
        "  pip install kaggle\n"
        "Then create an API token at https://www.kaggle.com/settings -> API\n"
        "and save it as ~/.kaggle/kaggle.json (on Windows: %USERPROFILE%\\.kaggle\\kaggle.json)."
    )
    sys.exit(1)


def detect_username(explicit: str | None) -> str:
    if explicit:
        return explicit
    try:
        output = subprocess.run(
            ["kaggle", "config", "view"], capture_output=True, text=True, check=True
        ).stdout
        for line in output.splitlines():
            if "username" in line.lower():
                return line.split(":", 1)[1].strip()
    except subprocess.CalledProcessError:
        pass
    username = input("Kaggle username not detected — please enter it: ").strip()
    if not username:
        print("Username required.")
        sys.exit(1)
    return username


def _push_kernel(
    notebook: Path, username: str, dataset_sources: list[str], machine_shape: str | None
) -> None:
    metadata = {
        "id": f"{username}/{KERNEL_SLUG}",
        "title": KERNEL_TITLE,
        "code_file": f"{KERNEL_SLUG}.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": True,
        "competition_sources": [],
        "dataset_sources": dataset_sources,
    }
    if machine_shape:
        metadata["machine_shape"] = machine_shape

    with tempfile.TemporaryDirectory(prefix="kaggle_translit_") as tmp:
        staging = Path(tmp)
        shutil.copy2(notebook, staging / f"{KERNEL_SLUG}.ipynb")
        (staging / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2))
        pushed = subprocess.run(
            ["kaggle", "kernels", "push", "-p", str(staging)],
            capture_output=True,
            text=True,
        )
        if pushed.returncode != 0:
            if machine_shape:
                print(
                    f"Push with machine_shape={machine_shape} failed "
                    f"({pushed.stderr.strip().splitlines()[-1] if pushed.stderr else 'unknown'}); "
                    "retrying with the default GPU shape."
                )
                _push_kernel(notebook, username, dataset_sources, machine_shape=None)
                return
            print(pushed.stdout, pushed.stderr)
            sys.exit(1)


def cmd_push(args: argparse.Namespace) -> None:
    require_kaggle()
    if not args.notebook.exists():
        print(f"Notebook not found: {args.notebook}")
        sys.exit(1)
    username = detect_username(args.user)
    _push_kernel(args.notebook, username, dataset_sources=[], machine_shape=_machine_shape(args.accelerator))

    print(f"\nPushed to https://www.kaggle.com/code/{username}/{KERNEL_SLUG}")
    print("Next steps in the Kaggle UI:")
    print("  1. Settings -> Accelerator -> GPU T4, Internet -> On")
    print("  2. Run All (the notebook downloads the Aksharantar Nepali data itself)")
    print("  3. When done, run:  python scripts/kaggle_transliterator.py pull")


def cmd_pull(args: argparse.Namespace) -> None:
    require_kaggle()
    if args.kernel is None:
        username = detect_username(None)
        args.kernel = f"{username}/{KERNEL_SLUG}"
    print(f"Downloading kernel output from {args.kernel} ...")
    subprocess.run(["kaggle", "kernels", "output", args.kernel, "-p", str(args.dest)], check=True)

    checkpoint = args.dest / "new_char_transformer_best.pt"
    vocab = args.dest / "new_char_vocab.pkl"
    if checkpoint.exists() and vocab.exists():
        print(f"Got {checkpoint.name} + {vocab.name} in {args.dest}")
        print("Now run:  python scripts/compare_transliterators.py")
    else:
        print(
            "Download finished but new_char_transformer_best.pt / new_char_vocab.pkl "
            "were not found. Did the training run complete on Kaggle?"
        )
        sys.exit(1)


def _machine_shape(accelerator: str) -> str | None:
    if accelerator == "t4":
        return "gpu_t4_2x"
    return None


def cmd_resume(args: argparse.Namespace) -> None:
    require_kaggle()
    username = detect_username(args.user)
    kernel = args.kernel or f"{username}/{KERNEL_SLUG}"
    resume_dataset = f"{username}/{RESUME_DATASET_SLUG}"

    if args.checkpoint is not None:
        checkpoint = args.checkpoint
        if not checkpoint.exists():
            print(f"Checkpoint not found: {checkpoint}")
            sys.exit(1)
    else:
        with tempfile.TemporaryDirectory(prefix="kaggle_resume_") as tmp:
            out_dir = Path(tmp) / "out"
            out_dir.mkdir()
            print(f"Pulling latest output of {kernel} ...")
            subprocess.run(
                ["kaggle", "kernels", "output", kernel, "-p", str(out_dir)], check=True
            )
            checkpoint = out_dir / "new_char_transformer_best.pt"
            if not checkpoint.exists():
                print(
                    "No new_char_transformer_best.pt found in the latest kernel output.\n"
                    "The previous run may still be RUNNING, errored before saving a "
                    "checkpoint, or was killed before any improvement. "
                    "Use --checkpoint PATH to resume from a local file."
                )
                sys.exit(1)

    with tempfile.TemporaryDirectory(prefix="kaggle_resume_") as tmp:
        ds_dir = Path(tmp) / "ds"
        ds_dir.mkdir()
        shutil.copy2(checkpoint, ds_dir / "new_char_transformer_best.pt")
        metadata = {
            "id": resume_dataset,
            "title": "Transliterator Resume Checkpoints",
            "isPrivate": True,
            "licenses": [{"name": "other"}],
        }
        (ds_dir / "dataset-metadata.json").write_text(json.dumps(metadata, indent=2))

        created = subprocess.run(
            ["kaggle", "datasets", "create", "-p", str(ds_dir)],
            capture_output=True,
            text=True,
        )
        combined = (created.stdout + created.stderr).lower()
        if created.returncode != 0 and "already exists" not in combined:
            print(created.stdout, created.stderr)
            sys.exit(1)
        if created.returncode != 0 or "already exists" in combined:
            print(f"Updating existing dataset {resume_dataset} ...")
            subprocess.run(
                ["kaggle", "datasets", "version", "-p", str(ds_dir), "-m", "resume checkpoint update"],
                check=True,
            )

    _push_kernel(DEFAULT_NOTEBOOK, username, dataset_sources=[resume_dataset], machine_shape=_machine_shape(args.accelerator))
    print(f"\nResume kernel pushed: https://www.kaggle.com/code/{username}/{KERNEL_SLUG}")
    print(
        "The notebook will copy the attached checkpoint into /kaggle/working and "
        "the trainer's built-in resume logic will continue from the saved epoch."
    )


def main() -> None:
    args = parse_args()
    if args.command == "push":
        cmd_push(args)
    elif args.command == "pull":
        cmd_pull(args)
    elif args.command == "resume":
        cmd_resume(args)


if __name__ == "__main__":
    main()
