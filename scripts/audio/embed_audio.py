"""Embed audio tracks with CLAP (resumable): audio -> 512-d joint text-audio vectors.

Reads R_data/audio/audio_tracks.csv, decodes 10 s clips with ffmpeg (imageio-ffmpeg
binary, no system install needed), and writes:
  - R_data/audio/audio_embeddings.npy   (N x 512 float32, L2-normalised)
  - R_data/audio/audio_embedding_keys.csv

Usage:
  python scripts/audio/embed_audio.py --limit 5          # smoke test
  python scripts/audio/embed_audio.py                    # full run (resumable)
  python scripts/audio/embed_audio.py --device cpu       # force CPU
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audio import config, utils  # noqa: E402

SAMPLE_RATE = config.SAMPLE_RATE
CLAP_MODEL = config.EMBEDDING_MODEL


def ffmpeg_exe() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def extract_segment(exe: str, path: Path, start: float, seconds: float = 10.0) -> "object | None":
    import numpy as np

    command = [
        exe, "-v", "error", "-ss", f"{max(start, 0):.2f}", "-t", f"{seconds:.2f}",
        "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SAMPLE_RATE), "pipe:1",
    ]
    try:
        proc = subprocess.run(command, capture_output=True, timeout=180)
    except subprocess.TimeoutExpired:
        return None
    if proc.returncode != 0 or not proc.stdout:
        return None
    audio = np.frombuffer(proc.stdout, dtype=np.float32)
    if audio.size < SAMPLE_RATE:  # less than 1 s decoded
        return None
    return audio


def offsets_for(duration: float, clips: int) -> list[float]:
    if duration >= 40:
        base = [0.25, 0.5, 0.75][:clips]
        return [max(0.0, duration * fraction - 5.0) for fraction in base]
    if duration >= 15:
        return [max(0.0, duration / 2 - 5.0)]
    return [0.0]


def feature_tensor(output):
    """transformers>=5 returns a ModelOutput; older versions return a tensor."""
    for key in ("pooler_output", "audio_embeds", "text_embeds"):
        value = output.get(key) if hasattr(output, "get") else getattr(output, key, None)
        if value is not None:
            return value
    return output


def load_existing() -> tuple[dict[str, "object"], list[dict]]:
    import numpy as np

    vectors_path = utils.AUDIO_DATA_DIR / "audio_embeddings.npy"
    keys_path = utils.AUDIO_DATA_DIR / "audio_embedding_keys.csv"
    vectors: dict[str, "object"] = {}
    rows: list[dict] = []
    if vectors_path.exists() and keys_path.exists():
        array = np.load(vectors_path)
        with open(keys_path, encoding="utf-8") as handle:
            loaded = list(csv.DictReader(handle))
        for index, row in enumerate(loaded):
            if index < len(array):
                vectors[row["track_key"]] = array[index]
                rows.append({**row, "status": "ok"})
    return vectors, rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sample", type=int, default=None)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--clips", type=int, default=3, help="clips per track (3 recommended)")
    parser.add_argument("--clip-seconds", type=float, default=10.0)
    parser.add_argument("--all", action="store_true", help="re-embed tracks that already have vectors")
    args = parser.parse_args()

    import numpy as np
    import torch
    from transformers import ClapModel, ClapProcessor

    tracks_path = utils.AUDIO_DATA_DIR / "audio_tracks.csv"
    if not tracks_path.exists():
        sys.exit(f"missing {tracks_path}; run build_manifest.py first")
    with open(tracks_path, encoding="utf-8") as handle:
        tracks = list(csv.DictReader(handle))
    with open(utils.AUDIO_DATA_DIR / "audio_manifest.csv", encoding="utf-8") as handle:
        manifest = list(csv.DictReader(handle))
    file_by_key: dict[str, list[dict]] = {}
    for item in manifest:
        file_by_key.setdefault(item["track_key"], []).append(item)

    vectors, rows = load_existing()
    pending = [t for t in tracks if args.all or t["track_key"] not in vectors]
    if args.sample:
        import random

        random.Random(args.seed).shuffle(pending)
        pending = pending[: args.sample]
    if args.limit:
        pending = pending[: args.limit]
    print(f"tracks: {len(tracks)} | embedded: {len(vectors)} | pending: {len(pending)}")
    if not pending:
        return

    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"device: {device} | model: {CLAP_MODEL}")
    processor = ClapProcessor.from_pretrained(CLAP_MODEL)
    model = ClapModel.from_pretrained(CLAP_MODEL).to(device).eval()
    exe = ffmpeg_exe()

    collection_root = utils.COLLECTION_ROOT
    started = time.time()
    processed = 0
    failures = 0
    for track in pending:
        files = file_by_key.get(track["track_key"], [])
        if not files:
            failures += 1
            continue
        path = collection_root / files[0]["audio_relpath"]
        duration = float(track["duration_s"] or 0.0)
        segments = []
        for offset in offsets_for(duration, args.clips):
            audio = extract_segment(exe, path, offset, args.clip_seconds)
            if audio is not None:
                segments.append(audio)
        if not segments:
            failures += 1
            rows.append({"track_key": track["track_key"], "artist": track["artist"], "title": track["title"],
                         "status": "decode_failed", "n_segments": 0, "path": files[0]["audio_relpath"]})
            continue
        with torch.no_grad():
            inputs = processor(audio=segments, sampling_rate=SAMPLE_RATE, return_tensors="pt")
            inputs = {key: value.to(device) for key, value in inputs.items()}
            output = model.get_audio_features(**inputs)
            vector = feature_tensor(output).mean(dim=0).float().cpu().numpy()
        norm = np.linalg.norm(vector)
        if norm:
            vector = vector / norm
        vectors[track["track_key"]] = vector.astype(np.float32)
        rows.append({"track_key": track["track_key"], "artist": track["artist"], "title": track["title"],
                     "status": "ok", "n_segments": len(segments), "path": files[0]["audio_relpath"]})
        processed += 1
        if processed % 25 == 0:
            elapsed = time.time() - started
            print(f"[{processed}/{len(pending)}] {processed/elapsed:.2f} tracks/s failures={failures}", flush=True)
            save(vectors, rows)

    save(vectors, rows)
    print(json.dumps({"embedded": processed, "failures": failures, "total_vectors": len(vectors)}, indent=2))


def save(vectors: dict, rows: list[dict]) -> None:
    import numpy as np

    keys = sorted(vectors)
    array = np.stack([vectors[key] for key in keys]).astype(np.float32)
    npy_path = utils.AUDIO_DATA_DIR / "audio_embeddings.npy"
    tmp_npy = npy_path.with_name("audio_embeddings.tmp.npy")
    np.save(tmp_npy, array)
    os.replace(tmp_npy, npy_path)
    row_by_key = {row["track_key"]: row for row in rows if row.get("status") == "ok"}
    keys_path = utils.AUDIO_DATA_DIR / "audio_embedding_keys.csv"
    tmp_csv = keys_path.with_suffix(".csv.tmp")
    with open(tmp_csv, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["track_key", "artist", "title", "path", "n_segments"])
        writer.writeheader()
        for key in keys:
            row = row_by_key.get(key, {"track_key": key})
            writer.writerow({"track_key": key, "artist": row.get("artist", ""), "title": row.get("title", ""),
                             "path": row.get("path", ""), "n_segments": row.get("n_segments", "")})
    os.replace(tmp_csv, keys_path)
    print(f"saved {array.shape} -> {npy_path}", flush=True)


if __name__ == "__main__":
    main()
