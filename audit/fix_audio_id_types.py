"""One-off repair: strip pandas float formatting from id columns in audio maps."""
from pathlib import Path

import pandas as pd

AUDIO = Path(r"D:\Code\ProjectR\R_data\audio")
TARGETS = {
    "audio_track_matches.csv": ["cand_song_id", "match_song_id", "final_song_id"],
    "audio_file_map.csv": ["cand_song_id", "match_song_id", "final_song_id"],
}
for name, columns in TARGETS.items():
    path = AUDIO / name
    frame = pd.read_csv(path, encoding="utf-8", dtype=str).fillna("")
    for column in columns:
        if column not in frame.columns:
            continue
        repaired = []
        for value in frame[column]:
            text = str(value).strip()
            if text.replace(".", "", 1).replace("-", "", 1).isdigit() and text.endswith(".0"):
                text = text[:-2]
            repaired.append(text)
        frame[column] = repaired
    frame.to_csv(path, index=False, encoding="utf-8")
    print(f"repaired {name}: {len(frame)} rows")
