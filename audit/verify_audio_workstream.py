"""Integrity verification for the audio workstream artifacts."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Code\ProjectR")
sys.path.insert(0, str(ROOT))

from scripts.audio import utils  # noqa: E402

AUDIO = ROOT / "R_data" / "audio"
checks: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    checks.append((name, bool(condition), detail))


# --- file presence ---
for name in [
    "audio_manifest.csv", "audio_tracks.csv", "audio_track_matches.csv",
    "audio_file_map.csv", "audio_new_songs_v2.csv", "audio_embeddings.npy",
    "audio_embedding_keys.csv", "audio_duplicate_candidates.csv",
    "audio_similarity_report.json", "manifest_report.json", "dataset_report.json",
]:
    check(f"exists:{name}", (AUDIO / name).exists(), "")

# --- row counts / cross-references ---
manifest = list(csv.DictReader(open(AUDIO / "audio_manifest.csv", encoding="utf-8")))
tracks = list(csv.DictReader(open(AUDIO / "audio_tracks.csv", encoding="utf-8")))
file_map = list(csv.DictReader(open(AUDIO / "audio_file_map.csv", encoding="utf-8")))
matches = list(csv.DictReader(open(AUDIO / "audio_track_matches.csv", encoding="utf-8")))
new_songs = list(csv.DictReader(open(AUDIO / "audio_new_songs_v2.csv", encoding="utf-8")))
keys = list(csv.DictReader(open(AUDIO / "audio_embedding_keys.csv", encoding="utf-8")))

check("manifest rows == 3663", len(manifest) == 3663, str(len(manifest)))
check("tracks rows == 3650", len(tracks) == 3650, str(len(tracks)))
check("file_map rows == manifest rows", len(file_map) == len(manifest), f"{len(file_map)}")
check("track_matches rows == tracks rows", len(matches) == len(tracks), f"{len(matches)}")
check("embedding keys == tracks", len(keys) == len(tracks), f"{len(keys)}")

import numpy as np  # noqa: E402

vectors = np.load(AUDIO / "audio_embeddings.npy")
check("embeddings shape (3650, 512)", vectors.shape == (3650, 512), str(vectors.shape))
check("embeddings finite", bool(np.isfinite(vectors).all()))
norms = np.linalg.norm(vectors, axis=1)
check("embeddings L2-normalised", bool(np.allclose(norms, 1.0, atol=1e-3)), f"min={norms.min():.4f} max={norms.max():.4f}")

# --- link integrity ---
corpus_ids = {int(row.song_id) for row in utils.load_corpus().itertuples()}
bad_links = {row["match_song_id"] for row in file_map if row["match_song_id"] and int(row["match_song_id"]) not in corpus_ids}
check("all linked song_ids exist in corpus", not bad_links, str(sorted(bad_links)[:5]))

new_ids = {row["audio_song_id"] for row in new_songs}
check("new song ids unique", len(new_ids) == len(new_songs), f"{len(new_ids)}/{len(new_songs)}")
check("new ids prefixed A-", all(sid.startswith("A-") for sid in new_ids))

mismatched = 0
for row in new_songs:
    expected = "A-" + hashlib.sha1(row["track_key"].encode("utf-8")).hexdigest()[:10]
    if row["audio_song_id"] != expected:
        mismatched += 1
check("new ids content-addressed (sha1 of track_key)", mismatched == 0, f"mismatched={mismatched}")

map_new_ids = {row["new_id"] for row in file_map if row["new_id"]}
check("file map new_ids match dataset lines", map_new_ids == new_ids, f"map={len(map_new_ids)} rows={len(new_ids)}")

dupes = [row for row in new_songs if not row["lyrics_devanagari"].strip()]
check("new dataset lines non-empty", not dupes, f"empty={len(dupes)}")

# --- lyrics cache ---
lyrics_rows = [json.loads(line) for line in open(AUDIO / "audio_lyrics.jsonl", encoding="utf-8") if line.strip()]
found = [row for row in lyrics_rows if row.get("found")]
check("lyrics jsonl found rows == 90", len(found) == 90, f"found={len(found)} total={len(lyrics_rows)}")

# --- coverage numbers ---
linked_files = sum(1 for row in file_map if row["match_song_id"])
new_files = sum(1 for row in file_map if row["new_id"])
print(f"coverage: {linked_files} files -> {len({row['match_song_id'] for row in file_map if row['match_song_id']})} corpus songs | "
      f"{new_files} files -> {len(new_ids)} new songs | unlinked {len(file_map) - linked_files - new_files}")

# --- git status summary ---
import subprocess  # noqa: E402

status = subprocess.run(["git", "status", "--short"], cwd=ROOT, capture_output=True, text=True).stdout
print("\ngit status (short):")
print(status or "(clean)")

failed = [name for name, ok, _ in checks if not ok]
for name, ok, detail in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
