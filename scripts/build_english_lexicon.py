"""Generate lyrics_pipeline/english_lexicon.py from the project transliterator.

The corpus transliteration model phonetically Devanagari-izes English words
(``this`` -> ``थिस``). This script builds two derived resources:

* ``ENGLISH_WORDS``: roman English tokens the transliteration gate must leave
  untouched (plus contraction suffixes handled contextually).
* ``ENGLISH_DEVANAGARI_FORMS`` / ``METADATA_DEVANAGARI_FORMS``: the model's own
  Devanagari renderings of English words, used to detect transliterated
  English prose and site metadata in already-transliterated text.

Words that collide with common romanized Nepali/Hindi tokens (``man`` -> मन,
``ma`` -> म, ``sun`` -> सुन, ...) are excluded from the gate, and Devanagari
forms that collide with common Nepali words (``आई`` from ``i``, ``हेरे`` from
``here``, ...) are excluded from detection.

Usage:
    python scripts/build_english_lexicon.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lyrics_pipeline.transliterator import NepaliTransliterator  # noqa: E402

OUT_PATH = PROJECT_ROOT / "lyrics_pipeline" / "english_lexicon.py"

CORE = """
the of and to in is it you that for on are as with they at be this have from or one had by
but not what all we when your can said there use each which she do how their if will up other
about out many then them these so some her would make like him into time has look two more
write go see number way could people my than first been call who its now find long down day
did get come made may part over new sound take only little work know place year live me back
give most very after thing our just name good through before much right too mean old any same
tell boy follow came want show also around form three small set put end does another well
large must big even such because turn here why ask went read need land different home move
try kind hand picture again change off play air away animal house point page letter mother
answer found study still learn should america world
love baby girl heart night life dream dreams soul eyes eye mind feel feeling feelings tonight
forever together alone stay miss missing hold holding break broken cry crying smile gone never
ever always sometimes maybe yeah oh ooh ah hey hello goodbye please sorry thank thanks okay
alright true truth lie lies bad better best sweet beautiful crazy shine star stars sky moon
rain fire burn dance dancing sing singing song songs music run running walk walking talk
talking say saying hear heard listen listening gotta gonna let dont cant wont aint im ive
ill id youre youve youll thats theres whoa lady ladies friends sunshine shadow light dark
darkness cold hot warm summer winter spring autumn morning evening midnight yesterday
tomorrow today remember forget forgive pain hurt hurts happy happiness sad sadness tears tear
laugh laughing kiss kisses hug touch closer close far high low fly flying angel heaven hell
devil god pray prayer faith hope wish wishes magic miracle wonderful amazing perfect pretty
cute honey darling dear shining burning falling calling waiting wanting needing living dying
breathing
think thing things thank believe wonder voice memory promise reason season word fear
""".split()

META = """
subscribe channel channels video videos lyric lyrics chords download downloads official
description descriptions comment comments notification bell facebook instagram twitter
youtube click link below above watch start timer contains hidden meaning translation
translated romanized romanization english language album released featuring artist artists
follow visit website content copyright report error recent years witnessed rise popular
genres genre pop rap hip hop remix version audio streaming stream playlist track share
shared sharing liked button buttons screen media social page pages online free top latest
hd hq mp3 quality movie film trailer teaser scene scenes credit credits vocal vocals singer
singers music director producer production studio recording mastering mixing composed composer
lyricist writer written performed performance cast starring actor actress
""".split()

CONTRACTIONS = [
    "don",
    "doesn",
    "didn",
    "can",
    "won",
    "isn",
    "ain",
    "wasn",
    "aren",
    "couldn",
    "wouldn",
    "shouldn",
]

CONTRACTION_SUFFIXES = ["t", "s", "d", "m", "ll", "ve", "re", "n"]

EXCLUDE_WORDS = {
    "a",
    "an",
    "o",
    "he",
    "us",
    "man",
    "men",
    "sun",
    "gun",
    "din",
    "tan",
    "pan",
    "jan",
    "kal",
    "mil",
    "nil",
    "har",
    "bar",
    "tar",
    "par",
    "kar",
    "nar",
    "sar",
    "ram",
    "ban",
    "ma",
    "na",
    "ta",
    "la",
    "ra",
    "re",
    "ga",
    "ja",
    "da",
    "pa",
    "ba",
    "ha",
    "sa",
    "ka",
    "ki",
    "ke",
    "ko",
    "ku",
    "cha",
    "yo",
    "ya",
    "de",
    "le",
    "ne",
    "te",
    "hu",
    "hun",
    "gai",
}

AMBIGUOUS_FORMS = {
    "\u0906\u0908",  # आई  (i)      -> Nepali "came"
    "\u0939\u0947",  # हे   (hey)    -> Nepali vocative
    "\u0939\u0930",  # हर   (her)    -> Nepali plural particle
    "\u0939\u0947\u0930\u0947",  # हेरे (here) -> Nepali "looked"
    "\u091f\u094b",  # टो   (to)
    "\u0938\u0947",  # से   (say)
    "\u0938\u094b",  # सो   (so)
    "\u092e\u0947",  # मे   (me/may)
    "\u0935\u0947",  # वे   (way/we)
    "\u0921\u094b",  # डो   (do)
    "\u092c\u093e\u0907",  # बाइ  (by)
}


def _format(values: list[str], per_line: int = 8, indent: str = "    ") -> str:
    lines = []
    for start in range(0, len(values), per_line):
        chunk = values[start : start + per_line]
        lines.append(indent + " ".join(f'"{value}",' for value in chunk))
    return "\n".join(lines)


def main() -> None:
    words = sorted(
        {word for word in (CORE + META + CONTRACTIONS) if word not in EXCLUDE_WORDS}
        | {"i"}
    )
    transliterator = NepaliTransliterator()
    if not transliterator.available:
        sys.exit("transliterator checkpoint not available; cannot build lexicon")
    forms = {word: transliterator.transliterate_word(word) for word in words}

    by_form: dict[str, list[str]] = {}
    for word, form in forms.items():
        by_form.setdefault(form, []).append(word)

    usable = {form: sorted(mapped) for form, mapped in by_form.items() if form not in AMBIGUOUS_FORMS}
    metadata_words = sorted({word for word in META if word in words})
    metadata_forms = sorted(
        {forms[word] for word in META if word in forms and forms[word] in usable}
    )

    body = f'''"""English vocabulary for the transliteration gate and artifact detection.

Generated by ``scripts/build_english_lexicon.py`` from the project
transliterator checkpoint; do not edit by hand. Regenerate after retraining
the transliterator.

``ENGLISH_WORDS`` keeps English tokens untouched during transliteration.
``ENGLISH_DEVANAGARI_FORMS`` / ``METADATA_DEVANAGARI_FORMS`` detect English
prose and site metadata that an earlier transliteration pass already turned
into Devanagari.
"""

ENGLISH_WORDS = frozenset(
{{
{_format(words)}
}}
)

ENGLISH_CONTRACTION_SUFFIXES = frozenset(
{{
{_format(CONTRACTION_SUFFIXES)}
}}
)

METADATA_WORDS = frozenset(
{{
{_format(metadata_words)}
}}
)

ENGLISH_DEVANAGARI_FORMS = frozenset(
{{
{_format(sorted(usable))}
}}
)

METADATA_DEVANAGARI_FORMS = frozenset(
{{
{_format(metadata_forms)}
}}
)

DEVANAGARI_FORM_TO_WORDS = {{
{chr(10).join(f'    "{form}": ({", ".join(repr(word) for word in mapped)}{"," if len(mapped) == 1 else ""}),' for form, mapped in sorted(usable.items()))}
}}
'''
    OUT_PATH.write_text(body, encoding="utf-8")
    print(f"wrote {OUT_PATH}")
    print(f"words {len(words)}  usable forms {len(usable)}  metadata forms {len(metadata_forms)}")


if __name__ == "__main__":
    main()
