"""CLAP cross-modal search over the local audio collection.

  python scripts/audio/query_audio.py --text "sad acoustic guitar" --k 10
  python scripts/audio/query_audio.py --like "Yama Buddha|saathi" --k 10
  python scripts/audio/query_audio.py --like-file path/to/track.mp3 --k 10

Requires audio_embeddings.npy / audio_embedding_keys.csv from embed_audio.py.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audio import utils  # noqa: E402
from scripts.audio.embed_audio import feature_tensor  # noqa: E402

CLAP_MODEL = "laion/clap-htsat-unfused"


def load_links() -> dict[str, dict]:
    path = utils.AUDIO_DATA_DIR / "audio_track_matches.csv"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as handle:
        return {row["track_key"]: row for row in csv.DictReader(handle)}


def load_tracks() -> dict[str, dict]:
    path = utils.AUDIO_DATA_DIR / "audio_tracks.csv"
    with open(path, encoding="utf-8") as handle:
        return {row["track_key"]: row for row in csv.DictReader(handle)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text")
    parser.add_argument("--like", help="track_key (artist|title, normalized) or substring")
    parser.add_argument("--like-file", type=Path, help="audio file to embed as the query")
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args()

    import numpy as np
    import torch
    from transformers import ClapModel, ClapProcessor

    vectors_path = utils.AUDIO_DATA_DIR / "audio_embeddings.npy"
    keys_path = utils.AUDIO_DATA_DIR / "audio_embedding_keys.csv"
    if not vectors_path.exists():
        sys.exit("no audio embeddings yet; run embed_audio.py")
    vectors = np.load(vectors_path)
    with open(keys_path, encoding="utf-8") as handle:
        keys = [row["track_key"] for row in csv.DictReader(handle)]
    norm = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / np.clip(norm, 1e-8, None)
    links = load_links()
    tracks = load_tracks()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    processor = ClapProcessor.from_pretrained(CLAP_MODEL)
    model = ClapModel.from_pretrained(CLAP_MODEL).to(device).eval()

    if args.text:
        with torch.no_grad():
            inputs = processor(text=[args.text], return_tensors="pt", padding=True)
            inputs = {key: value.to(device) for key, value in inputs.items()}
            text_output = model.get_text_features(**inputs)
            query = feature_tensor(text_output).float().cpu().numpy()[0]
        label = f"text: {args.text!r}"
    elif args.like or args.like_file:
        from scripts.audio.embed_audio import extract_segment, ffmpeg_exe, offsets_for

        if args.like_file:
            path = args.like_file
            duration = 60.0
        else:
            matches = [key for key in keys if args.like.lower() in key.lower()]
            if not matches:
                sys.exit(f"no track matches {args.like!r}")
            key = matches[0]
            track = tracks.get(key, {})
            path = utils.COLLECTION_ROOT / str(track.get("files", "")).split("|")[0]
            duration = float(track.get("duration_s") or 0.0)
        exe = ffmpeg_exe()
        segments = [segment for offset in offsets_for(duration, 3)
                    if (segment := extract_segment(exe, path, offset)) is not None]
        if not segments:
            sys.exit(f"could not decode {path}")
        with torch.no_grad():
            inputs = processor(audio=segments, sampling_rate=48000, return_tensors="pt")
            inputs = {key: value.to(device) for key, value in inputs.items()}
            audio_output = model.get_audio_features(**inputs)
            query = feature_tensor(audio_output).mean(dim=0).float().cpu().numpy()
        label = f"audio: {path.name}"
    else:
        sys.exit("pass --text, --like or --like-file")

    query = query / max(np.linalg.norm(query), 1e-8)
    scores = vectors @ query
    order = np.argsort(-scores)[: args.k]
    print(f"query {label}")
    for rank, index in enumerate(order, start=1):
        key = keys[index]
        link = links.get(key, {})
        track = tracks.get(key, {})
        target = link.get("match_song_id") or link.get("new_id") or ""
        artist = link.get("artist") or track.get("artist", "")
        title = link.get("title") or track.get("title", "")
        print(f"{rank:2d}. {scores[index]:.3f}  {artist[:30]:30s} - {title[:45]:45s}  song={target}")


if __name__ == "__main__":
    main()
