"""Cleaning and language-gate behavior for lyric text."""

from __future__ import annotations

import pytest

from lyrics_pipeline.cleaner import (
    clean_lyrics_body,
    is_english_prose_line,
    is_noise_line,
)
from lyrics_pipeline.transliterator import NepaliTransliterator


def test_clean_lyrics_body_removes_scrape_artifacts() -> None:
    body = "\n".join(
        [
            "माया को गीत गाउँछु",
            "डाउनलोड लिरिक्स",
            "क्लिक हेरे टु गेट मोर",
            "स्टार्ट टाइमर फोर डाउनलोड",
            "वाच ओन युट्युब",
            "यो गीत #हिट #नेपाल",
            "#पुष्पनप्रधान #नजिरहुसेन",
            "🎬 विदेओ क्रेडिट्स",
            "♪ वोकल: राम",
            "यो माया हो 🎬",
            "एचटीटीपीएस://डब्ल्यूडब्ल्यू.युट्युब.सीओएम",
            "साथी भेट https://example.com/g",
            "बिशाल निरोउला",
            "म्युजिक विदेओ",
            "म्युजिक बजाउँदै नाच",
            "राम्रो गीत गाउँछुएम्बेड",
            "2 कन्ट्रिब्युटर्ससप लिरिक्सचारैतिर अध्यारो",
            "1 ContributorDashain Aayo Lyrics[Pre-Chorus]",
            "Song:- मायालु",
            "Music Arranger:- Prashant Poudel",
            "Discription of Video",
            "Description of Video",
            "Romanize",
            "NEPALI VERSION",
            "Special ThanksBijaya Adhikari",
            "Asst. Choreographer: Roshan Bishwokarma",
            "Cinematographer Ram Thapa",
            "Post Production",
            "-Lyrics: बिरेन्द्र डोङ",
            "► Lyrics: दिग्गज धुराली",
            "सारंगी : मनिष गन्दर्व",
            "हो हो हो हो हो हो हो",
            "1 कन्ट्रिब्युटरनेपा हो लिरिक्स[चोरुस]",
            "पुरानो बास्न लिरिक्स | अंकिता पुन",
        ]
    )
    cleaned, actions = clean_lyrics_body(body, "टेस्ट गीत", "कलाकार")
    lines = [line for line in cleaned.splitlines() if line.strip()]
    assert lines == [
        "माया को गीत गाउँछु",
        "यो गीत",
        "यो माया हो",
        "साथी भेट",
        "म्युजिक बजाउँदै नाच",
        "राम्रो गीत गाउँछु",
        "चारैतिर अध्यारो",
        "हो हो हो हो हो हो हो",
    ]
    assert actions


def test_lyric_repeats_and_phrases_survive() -> None:
    for line in ("हो हो हो हो हो हो हो", "तिमीलाई तिमीलाई", "ला ला ला ला ला"):
        assert not is_noise_line(line, "", "")

    assert not is_noise_line("म्युजिक बजाउँदै नाच", "", "")
    assert is_noise_line("म्युजिक विदेओ", "", "")
    assert is_noise_line("बिशाल निरोउला", "", "")
    assert is_noise_line("#पुष्पनप्रधान #नजिरहुसेन", "", "")


def test_english_prose_line_detection() -> None:
    prose = (
        "योउ मे सब्सक्राइब थिस च्यानल फोर न्यू एन्ड ओल्ड विदेओस् ओएफ हेमान्ट शर्मा"
    )
    assert is_english_prose_line(prose)

    assert not is_english_prose_line("आइ लभ योउ")
    assert not is_english_prose_line("तिमीलाई माया गर्छु सधैं")
    assert not is_english_prose_line("राम्रो गीत गाउँछु")


@pytest.fixture(scope="module")
def transliterator() -> NepaliTransliterator:
    engine = NepaliTransliterator()
    if not engine.available:
        pytest.skip("transliterator checkpoint not available")
    return engine


def test_transliteration_gate_keeps_english(transliterator: NepaliTransliterator) -> None:
    assert transliterator.transliterate_text("I love you baby") == "I love you baby"
    assert (
        transliterator.transliterate_text("don't you know my name")
        == "don't you know my name"
    )
    assert transliterator.transliterate_text("you are my sunshine") == "you are my sunshine"
    assert transliterator.transliterate_text("here comes the sun") == "here comes the सुन"
    english_line = (
        "Sunday morning I met a man with a top hat and a tail coat walking down the road"
    )
    assert transliterator.transliterate_text(english_line) == english_line


def test_transliteration_gate_transliterates_mixed_nepali(
    transliterator: NepaliTransliterator,
) -> None:
    output = transliterator.transliterate_text("I love you bhanne geet")
    assert "I love you" in output
    assert "bhanne" not in output
    assert "geet" not in output


def test_transliteration_gate_still_converts_nepali(
    transliterator: NepaliTransliterator,
) -> None:
    output = transliterator.transliterate_text("timi lai maya garchu")
    assert "timi" not in output
    assert "timi" not in output.lower()
    assert "तिमी" in output
