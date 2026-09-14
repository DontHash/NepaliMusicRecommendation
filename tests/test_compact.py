"""Tests for corpus compaction and pipeline provenance pass-through."""

from __future__ import annotations

from data_collection import state
from data_collection.compact import compact
from data_collection.models import Candidate, LyricsHit
from data_collection.normalize import lyrics_sha
from lyrics_pipeline.pipeline import LyricsCleaningPipeline


class StubTransliterator:
    available = False


def _add(conn, source, artist, title, lyrics, script="devanagari", duration=None):
    cand = Candidate(source=source, artist=artist, title=title, duration_s=duration)
    state.enqueue(conn, [cand])
    row = state.get_by_dedupe_key(conn, cand.dedupe_key)
    state.save_lyrics(
        conn,
        row["id"],
        LyricsHit(stage="test_stage", lyrics=lyrics, script=script, sha256=lyrics_sha(lyrics)),
    )


def test_compact_dedupes_and_filters(tmp_path):
    conn = state.open_db(tmp_path / "db.sqlite")
    state.init_db(conn)
    dev = "माया लाग्छ तिम्रो मन " * 20
    _add(conn, "deezer", "A", "Song", dev, duration=200)
    _add(conn, "itunes", "A", "Song", dev + " फेरि", duration=240)
    _add(conn, "deezer", "B", "English", "hello world this is english " * 20, script="romanized")
    _add(conn, "deezer", "C", "Short", "माया", script="devanagari")
    out = tmp_path / "corpus_raw.csv"
    report = compact(conn, out)
    assert report["kept"] == 1
    assert report["dropped_script"] == 1
    assert report["dropped_short"] == 1
    assert report["dropped_near_duplicate"] == 1
    content = out.read_text(encoding="utf-8")
    assert "source_url" in content and "sha256" in content and "preview_url" in content
    assert (tmp_path / "snapshots").exists()
    assert report["sha256"]


def test_pipeline_passes_extra_columns(tmp_path):
    inp = tmp_path / "in.csv"
    inp.write_text(
        "Category,Title,Artist,Lyrics,source,stage\n"
        "nepali,My Song,Some Artist,माया लाग्छ तिम्रो मन,site_test,site_paankopat.com\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.csv"
    pipeline = LyricsCleaningPipeline(transliterator=StubTransliterator(), transliterate=False)
    summary = pipeline.process_file(inp, out, extra_columns=("source", "stage"))
    assert summary["total_rows"] == 1
    text = out.read_text(encoding="utf-8")
    assert "site_test" in text and "site_paankopat.com" in text
    assert "lyrics_devanagari" in text
