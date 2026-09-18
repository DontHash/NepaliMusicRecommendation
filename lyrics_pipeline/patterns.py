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

# Credit/metadata lines seen on the crawler sites ("Lyrics: X", "Cast: ...",
# "शब्द र संगीत: ..."). The ambiguous labels require a separator, so lyric
# lines like "शब्द केलाउ" or "संगीत अमर कर दो" survive.
CREDIT_LINE_PATTERNS = (
    re.compile(
        r"^(?:Lyrics?|Singers?|Cast|Casts?|Actors?|Actress|Music|Composer|Composed|Composition|"
        r"Director|Producer|Starring|Vocals?|Songwriter|"
        r"शब्द|संगीत|संगीतकार|गायक|गायिका|कलाकार|एक्टर्स|निर्देशक|निर्माता|लिरिक्स|"
        r"सोङ|एरेन्जर|एरेन्ज|मास्टरिङ|रेकर्डिस्ट|रेकर्डिङ|स्टुडियो|डाइरेक्टर|डाइरेक्सन|"
        r"क्यामेरा|पब्लिसिटी|म्यानेजमेन्ट|प्रोड्युसर|प्रोडक्सन|कोरियोग्राफर|वोकल|"
        r"सिनेमाटोग्राफर|सिनेमेटोग्राफी|ब्याकग्राउन्ड|कोपीराइट|डिजिटल|डिजाइन|विजुअल|"
        r"एडिट|कलरिस्ट|आर्टिस्ट|एक्जिक्युटिभ|स्टोरी|कन्सेप्ट|ट्रान्सपोर्टेसन)"
        r"\s*[:：\-–].*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:Lyrics?|Singers?|शब्द)\s*(?:/|,|&|\band\b|\sर\s)\s*"
        r"(?:Music|Songwriter|Composer|Composition|संगीत)\s*[:：\-–]?",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:Singers?|Starring|Cast|Casts?|Actors?|Actress|"
        r"कोरियोग्राफर|सिनेमाटोग्राफर|सिनेमेटोग्राफी|डाइरेक्टर|डाइरेक्सन|निर्देशक|"
        r"प्रोड्युसर|कलरिस्ट|एडिटर|फ्लुट|आर्टिस्ट|पब्लिसिटी|म्यानेजमेन्ट|एक्शन|"
        r"स्टोरी|कन्सेप्ट|एक्जिक्युटिभ|प्रोडक्सन|रेकर्डिङ|मिक्सिङ|कोपीराइट|आर्ट)\s+\S",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:Singers?|Casts?|Actors?|Music|Lyrics?|Starring|"
        r"कोरियोग्राफर|सिनेमाटोग्राफर|एरेन्जर|मास्टरिङ|स्टुडियो)$",
        re.IGNORECASE,
    ),
)

# Crawler-site title junk ("X lyrics / Artist", "X Lyrics and Chords",
# "X [Chords] - SiteName"). Everything from the first lyrics/chords marker on
# is metadata; the prefix is kept.
TITLE_JUNK_RE = re.compile(
    r"\s*[\(\[/\-–—,]*\s*\b(?:official\s+)?"
    r"(?:lyric\s*video|lyrics?(?:\s*(?:and|&|/|,)?\s*(?:chords?|music|video))?|chords?)"
    r"\b.*$",
    re.IGNORECASE,
)
LYRICS_OF_RE = re.compile(r"^\s*lyrics?\s+of\s+(.+?)(?:\s+(?:from|by|in)\b.*)?$", re.IGNORECASE)

# Crawler-site boilerplate. Sites append download/watch instructions and
# credit blocks; some pass through the transliterator before reaching the
# cleaner, so both English and Devanagari forms are matched.
CRAWLER_FOOTER_PATTERNS = (
    re.compile(r"^डाउनलोड\s*लिरिक्स$", re.IGNORECASE),
    re.compile(r"^क्लिक\s*हेरे.*$", re.IGNORECASE),
    re.compile(r"^स्टार्ट\s*टाइमर.*$", re.IGNORECASE),
    re.compile(r"^वाच\s*ओन.*$", re.IGNORECASE),
    re.compile(r"^बेस्ट\s+हेडफोन्स.*$", re.IGNORECASE),
    re.compile(r"^फाउन्ड\s+अन\s+एरर\s+रिपोर्ट.*$", re.IGNORECASE),
    re.compile(r"^Download\s+Lyrics$", re.IGNORECASE),
    re.compile(r"^Click\s+here.*$", re.IGNORECASE),
    re.compile(r"^Start\s+timer.*$", re.IGNORECASE),
    re.compile(r"^Watch\s+on\s+YouTube.*$", re.IGNORECASE),
)

URL_RE = re.compile(
    r"(?:https?://\S+|www\.\S+|"
    r"(?:एचटीटीपी|डब्ल्यूडब्ल्यूडब्ल्यू|डब्लुडब्लु|हट्टप)[^\s]*)",
    re.IGNORECASE,
)

EMOJI_RE = re.compile(
    "[\U0001f300-\U0001faff\u2600-\u27bf\ufe0f\u2190-\u21ff\u2b00-\u2bff]"
)
MUSIC_NOTE_RE = re.compile(r"[♬♪♩♫]")

HASHTAG_RE = re.compile(r"(?<!\w)#\S+")
HASHTAG_ONLY_RE = re.compile(r"^#\S+(?:\s+#\S+)*$")

EMBED_SUFFIX_RE = re.compile(r"\s*[\(\[]?(?:नएम्बेड|एम्बेड|[Ee]mbed)[\)\]]?\s*$")

CONTRIBUTOR_PREFIX_RE = re.compile(
    r"^\d+\s*कन्ट्रिब्युटरस?[^\n]*?लिरिक्स\s*(?:\[[^\]]*\])?",
    re.IGNORECASE,
)

LYRICS_LABEL_RE = re.compile(r"लिरिक्स\s*[|｜]")

TRAILING_VIDEO_RE = re.compile(
    r"\s*[-–—|]+\s*(?:विदेओ|वीडियो|[Vv]ideo|[Oo]fficial\s+[Vv]ideo)\s*(?:\|.*)?$",
    re.IGNORECASE,
)

# Scraped title suffixes frequently repeated inside lyrics bodies.
TITLE_NOISE_SUFFIXES = (
    " lyrics",
    " - lyrics",
    " (romanized)",
    " (नेपाली आनुवाद)",
    ", nepali song",
)
