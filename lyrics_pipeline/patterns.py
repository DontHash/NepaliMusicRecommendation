"""Regex patterns and constants for Genius-scraped Nepali lyrics."""

import re

# Zero-width and odd space characters seen in scraped lyrics.
INVISIBLE_CHARS_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]")

# Normalize curly / typographic quotes to ASCII equivalents before optional removal.
QUOTE_MAP = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201a": "'",
        "\u201b": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u201e": '"',
        "\u2032": "'",
        "\u2033": '"',
        "\u00ab": '"',
        "\u00bb": '"',
    }
)

CONTRIBUTOR_LINE_RE = re.compile(r"^\d+\s+Contributors?$", re.IGNORECASE)
TRANSLATIONS_HEADER_RE = re.compile(r"^Translations$", re.IGNORECASE)
SECTION_BRACKET_RE = re.compile(r"^\[[^\]]+\]\s*$")
SECTION_WORD_RE = re.compile(
    r"^(Verse|Chorus|Bridge|Intro|Outro|Hook|Pre-Chorus|PRE Chorus|Interlude|Skit|"
    r"Refrain|Post-Chorus|Sample|Instrumental)\b[^[\n]*$",
    re.IGNORECASE,
)
PAREN_ENGLISH_TRANSLATION_RE = re.compile(r"\([^)]*[A-Za-z][^)]*\)")
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
ROMAN_RE = re.compile(r"[A-Za-z]")
ROMAN_TOKEN_RE = re.compile(r"[A-Za-z]+")
TITLE_SUFFIX_RE = re.compile(
    r"\s*[\(\-–—,]*\s*(Romanized|नेपाली आनुवाद|Nepali Song|Nepali Lyrics)\s*[\)]?\s*$",
    re.IGNORECASE,
)
GENIUS_ARTIST_MARKERS = (
    "genius nepali translations",
    "genius romanizations",
    "genius translations",
)

# Lines that are metadata echoes rather than lyrical content.
METADATA_LINE_PATTERNS = (
    re.compile(r"^You might also like", re.IGNORECASE),
    re.compile(r"^Embed$", re.IGNORECASE),
    re.compile(r"^See .+ on Genius$", re.IGNORECASE),
    re.compile(r"^Read More$", re.IGNORECASE),
)

# Scraped title suffixes frequently repeated inside lyrics bodies.
TITLE_NOISE_SUFFIXES = (
    " lyrics",
    " - lyrics",
    " (romanized)",
    " (नेपाली आनुवाद)",
    ", nepali song",
)
