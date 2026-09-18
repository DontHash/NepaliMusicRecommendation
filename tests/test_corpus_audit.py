"""Checks for the corpus quality audit heuristics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.audit_corpus_quality import find_shared_templates, scan_corpus

FOOTER = "डाउनलोड लिरिक्स"
TIMER = "स्टार्ट टाइमर फोर डाउनलोड"
REFRAIN = "हो हो हो हो हो हो हो"


def _write_corpus(tmp_path: Path) -> tuple[Path, Path]:
    songs = {
        0: f"राम्रो माया को गीत\n{FOOTER}\n{TIMER}",
        1: f"फूल झैँ फुल्यो मन\n{FOOTER}\n{TIMER}",
        2: f"नदी बग्छ सधैं\n{FOOTER}\n{TIMER}",
        3: f"सपना देखेँ रातमा\n{FOOTER}",
        4: f"तारा चम्किन्छ आकाशमा\n{FOOTER}",
        5: f"क्रेडिट्स: गायक\n{FOOTER}\n{TIMER}\n#नेपालिसंग\nएक हरफ मात्र गीत",
        6: f"{REFRAIN}\nबाटो लामो छ",
        7: f"{REFRAIN}\nघाम अस्ताउँदै छ",
        8: f"{REFRAIN}\nहावा चिसो छ",
    }
    cleaned = pd.DataFrame(
        {
            "song_id": list(songs),
            "title": [f"Song {index}" for index in songs],
            "artist": [f"Artist {index}" for index in songs],
            "category": ["nepali"] * len(songs),
            "lyrics": list(songs.values()),
            "token_count": [10] * len(songs),
        }
    )
    corpus_final = pd.DataFrame(
        {
            "title_clean": cleaned["title"],
            "artist_clean": cleaned["artist"],
            "source": ["site_example.com"] * len(songs),
        }
    )
    cleaned_path = tmp_path / "cleaned_lyrics.csv"
    final_path = tmp_path / "corpus_final.csv"
    cleaned.to_csv(cleaned_path, index=False, encoding="utf-8")
    corpus_final.to_csv(final_path, index=False, encoding="utf-8")
    return cleaned_path, final_path


def test_find_shared_templates_counts_distinct_songs() -> None:
    songs = [
        (0, f"{FOOTER}\nराम्रो"),
        (1, f"{FOOTER}\nमीठो"),
        (2, f"{FOOTER}\nमीठो दोहोरो"),
    ]
    templates = find_shared_templates(songs, min_songs=3, min_chars=8)
    assert FOOTER in templates
    assert templates[FOOTER] == {0, 1, 2}
    assert "मीठो" not in templates


def test_scan_corpus_flags_artifacts_and_quarantine(tmp_path: Path) -> None:
    cleaned_path, final_path = _write_corpus(tmp_path)
    report, songs = scan_corpus(
        cleaned_path,
        final_path,
        min_songs_template=3,
        min_template_chars=8,
        artifact_ratio=0.5,
        top_templates=10,
    )
    assert report["total_songs"] == 9
    assert report["songs_with_artifacts"] >= 6
    assert report["patterns"]["crawler_footer"]["songs"] >= 6

    footer_rows = [row for row in report["shared_templates"]["top"] if row["line"] == FOOTER]
    assert footer_rows and footer_rows[0]["metadata_like"] is True
    refrain_rows = [row for row in report["shared_templates"]["top"] if row["line"] == REFRAIN]
    assert refrain_rows and refrain_rows[0]["metadata_like"] is False

    song = songs.set_index("song_id")
    assert song.loc[0, "artifact_lines"] == 2
    assert song.loc[6, "repeat_lines"] == 1
    assert song.loc[6, "artifact_lines"] == 0
    assert song.loc[5, "quarantine"] is True or bool(song.loc[5, "quarantine"])
    assert "artifact ratio" in song.loc[5, "quarantine_reason"]
