"""Hermetic tests for scripts/audio (no collection, no model downloads)."""

from __future__ import annotations

import json

import pytest

from scripts.audio import config, utils
from scripts.audio.build_dataset_lines import decide
from scripts.audio.build_manifest import classify, load_index, load_metadata_csv
from scripts.audio.embed_audio import feature_tensor, offsets_for
from scripts.audio.fetch_lyrics import already_done


# --- normalization / metadata -------------------------------------------------

def test_strip_junk_and_pipes():
    raw = "Timi Saath Huda || BEHULI Movie Song 2026 | Official Music Video"
    assert utils.strip_junk(raw) == "Timi Saath Huda"


def test_primary_artist_variants():
    assert utils.primary_artist("Bipul Chettri & Friends feat. X") == "Bipul Chettri"
    assert utils.primary_artist("A, B, C") == "A"
    assert utils.primary_artist("Yama Buddha ft. Mistah K") == "Yama Buddha"
    assert utils.primary_artist("Solo Artist") == "Solo Artist"


def test_parse_filename_forms():
    assert utils.parse_filename("Narayan Gopal - Euta Manche Ko Mayale.mp3") == (
        "Narayan Gopal", "Euta Manche Ko Mayale")
    assert utils.parse_filename("unknown - name (2).m4a") == ("unknown", "name (2)")
    assert utils.parse_filename("NoSeparator.mp3") == ("", "NoSeparator")


def test_track_key_is_stable_and_normalized():
    first = utils.track_key("Yam Baral", "Dukha Pani Ropeyo")
    second = utils.track_key("  yam baral ", "dukha pani ropeyo (2)")
    assert first == second


def test_is_generic_title():
    assert utils.is_generic_title("Maya")
    assert not utils.is_generic_title("Resham Firiri")


# --- provider lyrics sanitisation --------------------------------------------

def test_sanitize_provider_lyrics_drops_lrc_and_cjk():
    raw = "\n".join([
        "[00:12.50]तिम्रो माया",
        "作词 : Someone",
        "作曲 : Someone",
        "只中文字幕行",
        "तिम्रो माया",
        "I won't let go",
    ])
    clean = utils.sanitize_provider_lyrics(raw)
    assert clean == "तिम्रो माया\nतिम्रो माया\nI won't let go"


def test_devanagari_share():
    assert utils.devanagari_share("तिम्रो माया") == 1.0
    assert utils.devanagari_share("only english words") == 0.0
    assert utils.devanagari_share("") == 0.0


def test_nepali_ratio_distinguishes_english_from_romanized():
    english = "I sway in the darkness\nTo the rhythm of the rain\nAnd I was in the garden"
    romanized = "piuda piudai jindagi yo rityauna chahanchhu ma\nma timi lai maya garchu hai"
    assert utils.nepali_ratio(english) < 0.5
    assert utils.nepali_ratio(romanized) >= 0.5
    assert utils.nepali_ratio("तिम्रो माया") == 1.0
    assert utils.nepali_ratio("") == 1.0


# --- matching / verdicts ------------------------------------------------------

def test_classify_buckets():
    assert classify(95, 95, True, "Resham Firiri") == "strong"
    assert classify(80, 80, True, "Some Song") == "probable"
    assert classify(66, 40, True, "Some Song") == "weak"
    assert classify(20, 20, True, "Some Song") == "none"
    # no artist: needs a distinctive title at 95
    assert classify(96, 0, False, "Resham Firiri") == "strong"
    assert classify(96, 0, False, "Maya") == "probable"


def test_decide_verdicts():
    assert decide(90, 0, 1.0, True) == "lyrics_confirmed"
    assert decide(10, config.CONFIRM_SIM_METADATA, 1.0, True) == "lyrics_confirmed"
    assert decide(50, 0, 1.0, True) == "lyrics_ambiguous_linked"
    # language gate runs before ambiguous linking: an English track with
    # moderate token overlap must not be linked to a Nepali corpus song
    assert decide(50, 0, 0.2, True) == "new_lyrics_non_nepali"
    assert decide(10, 0, 0.1, False) == "new_lyrics_non_nepali"
    assert decide(10, 0, 0.9, False) == "new_lyrics"


def test_load_metadata_csv_aliases(tmp_path):
    path = tmp_path / "library.csv"
    path.write_text(
        "audio_path,artist,title,duration_s\n"
        "C:/music/A.mp3,Artist One,Title One,215\n"
        "C:/music/sub/B.m4a,Artist Two,Title Two,180\n",
        encoding="utf-8",
    )
    rows = load_metadata_csv(path)
    assert rows["a.mp3"]["author"] == "Artist One"
    assert rows["b.m4a"]["title"] == "Title Two"
    assert rows["b.m4a"]["duration"] == "180"


def test_load_index_missing_returns_empty(tmp_path):
    assert load_index(tmp_path) == {}


# --- embedding helpers ---------------------------------------------------------

def test_offsets_for():
    assert len(offsets_for(60.0, 3)) == 3
    assert len(offsets_for(20.0, 3)) == 1
    assert offsets_for(5.0, 3) == [0.0]
    for offset in offsets_for(60.0, 3):
        assert 0.0 <= offset <= 55.0


def test_feature_tensor_extracts_pooler_output():
    torch = pytest.importorskip("torch")

    tensor = torch.ones(2, 4)
    assert feature_tensor(tensor) is tensor
    assert feature_tensor({"pooler_output": tensor}) is tensor

    class Output:
        pooler_output = tensor

    assert feature_tensor(Output()) is tensor


# --- resumability ---------------------------------------------------------------

def test_already_done_resume(tmp_path):
    path = tmp_path / "lyrics.jsonl"
    path.write_text(
        json.dumps({"track_key": "a|b"}) + "\n"
        + "{not json}\n"
        + json.dumps({"track_key": "c|d"}) + "\n",
        encoding="utf-8",
    )
    assert already_done(path) == {"a|b", "c|d"}
    assert already_done(tmp_path / "missing.jsonl") == set()
