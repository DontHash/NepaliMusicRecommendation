"""Final summary of the audio<->lyrics run for the report."""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Code\ProjectR")
sys.path.insert(0, str(ROOT))

from scripts.audio import utils  # noqa: E402

audio_dir = ROOT / "R_data" / "audio"
files = list(csv.DictReader(open(audio_dir / "audio_file_map.csv", encoding="utf-8")))
tracks = list(csv.DictReader(open(audio_dir / "audio_track_matches.csv", encoding="utf-8")))
new = list(csv.DictReader(open(audio_dir / "audio_new_songs_v2.csv", encoding="utf-8")))

linked_files = [f for f in files if f["match_song_id"]]
new_files = [f for f in files if f["new_id"]]
unlinked = [f for f in files if not f["match_song_id"] and not f["new_id"]]
print("files:", len(files))
print("  linked to existing song:", len(linked_files))
print("  new song (A-*):", len(new_files))
print("  unlinked:", len(unlinked))
print("  distinct existing songs covered:", len({f['match_song_id'] for f in linked_files}))
print("  distinct new songs:", len({f['new_id'] for f in new_files}))

print("\nverdicts:", dict(Counter(t["match_basis"] for t in tracks)))

print("\nconfirmed/ambiguous links (lyrics similarity):")
for t in tracks:
    if t["match_basis"] in {"lyrics_confirmed", "lyrics_ambiguous_linked"}:
        print(f"  {t['match_basis']:26s} sim={t['lyrics_sim']:>6}  {t['artist'][:24]:24s} - {t['title'][:34]:34s} -> song {t['match_song_id']}")

print("\nnew dataset lines (first 12):")
for row in new[:12]:
    print(f"  {row['audio_song_id']}  {row['artist_clean'][:22]:22s} - {row['title_clean'][:32]:32s}  lines={row['line_count']:>3} tokens={row['token_count']:>4} src={row['lyrics_source']}")

sim_report = audio_dir / "audio_similarity_report.json"
if sim_report.exists():
    import json

    report = json.loads(sim_report.read_text(encoding="utf-8"))
    print(f"\nduplicate pairs >= {report['threshold']}: {report['duplicate_pairs']}")
