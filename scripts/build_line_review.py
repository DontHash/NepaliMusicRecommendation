"""Generate the line-gold review kit (CSV + Markdown) with model picks attached.

Reads ``eval/line_mood_gold.csv``, probes each song with the current attribution
engine, and writes:

- ``eval/line_mood_review.csv`` — gold rows plus the probe's current per-line
  pick and probabilities, with empty ``user_emotion`` / ``user_note`` columns
  for the human review pass.
- ``eval/line_mood_review.md`` — the same content grouped per song for reading
  (and for pasting into an external checker).

Usage:
    python scripts/build_line_review.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from music_rec.mood_attribution import EMOTIONS, MoodAttributor

GOLD = PROJECT_ROOT / "eval" / "line_mood_gold.csv"
SONG_GOLD = PROJECT_ROOT / "eval" / "mood_gold.csv"
OUT_CSV = PROJECT_ROOT / "eval" / "line_mood_review.csv"
OUT_MD = PROJECT_ROOT / "eval" / "line_mood_review.md"


def main() -> None:
    gold = pd.read_csv(GOLD, encoding="utf-8")
    song_gold = pd.read_csv(SONG_GOLD, encoding="utf-8").set_index("song_id")
    attributor = MoodAttributor()
    attributor._load_corpus_artifacts()

    payloads: dict[int, dict] = {}
    rows: list[dict] = []
    for row in gold.itertuples():
        if row.song_id not in payloads:
            payloads[row.song_id] = attributor.attribute_song(row.song_id)
        line = payloads[row.song_id]["lines"][row.line_index]
        probs = line["probs"]
        model_pick = line["dominant"]
        model_probs = " | ".join(f"{e} {probs[e]:.2f}" for e in EMOTIONS)
        g = song_gold.loc[row.song_id]
        rows.append(
            {
                "song_id": row.song_id,
                "title": row.title,
                "artist": row.artist,
                "line_index": row.line_index,
                "text": row.text,
                "occurrences": row.occurrences,
                "primary_emotion": row.primary_emotion,
                "polarity": row.polarity,
                "cue_type": row.cue_type,
                "difficulty": row.difficulty,
                "notes": row.notes,
                "song_primary": g["primary_emotion"],
                "song_polarity": g["polarity"],
                "song_notes": g["notes"],
                "model_pick": model_pick,
                "model_probs": model_probs,
                "user_emotion": "",
                "user_note": "",
            }
        )
    review = pd.DataFrame(rows)
    review.to_csv(OUT_CSV, index=False, encoding="utf-8")

    lines: list[str] = [
        "# Line mood gold — review sheet (agent_v1)",
        "",
        "Review rules live in `eval/line_mood_policy.md`. Fill `user_emotion` /",
        "`user_note` in `eval/line_mood_review.csv` where you disagree; empty",
        "`user_emotion` means the agent label is accepted. `model_pick` is the",
        "current probe's per-line guess for context.",
        "",
    ]
    for song_id, group in review.groupby("song_id", sort=False):
        head = group.iloc[0]
        lines.append(f"## {song_id} · {head['title']} — {head['artist']}")
        lines.append("")
        lines.append(
            f"Song gold: **{head['song_primary']}** ({head['song_polarity']})"
            f" — {head['song_notes']}"
        )
        lines.append("")
        lines.append("| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |")
        lines.append("|----:|--:|------|-------|-------|---------------|-----|------|------|")
        for row in group.itertuples():
            probs = row.model_probs.replace(" | ", " ")
            note = str(row.notes).replace("|", "/")
            text = row.text.replace("|", "/")
            lines.append(
                f"| {row.line_index} | {row.occurrences} | {text} | {row.primary_emotion} "
                f"| {row.model_pick} | {probs} | {row.cue_type} | {row.difficulty} | {note} |"
            )
        lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    scored = review[review["cue_type"] != "artifact"]
    agree = (scored["model_pick"] == scored["primary_emotion"]).sum()
    print(f"wrote {len(review)} rows -> {OUT_CSV}")
    print(f"wrote review sheet -> {OUT_MD}")
    print(f"current model agreement (artifacts excluded): {agree}/{len(scored)} = {agree / len(scored):.3f}")


if __name__ == "__main__":
    main()
