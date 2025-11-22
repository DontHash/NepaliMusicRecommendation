import re
import csv
from collections import defaultdict


DEV_CONSONANTS = {
    # Velars
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "ṅ",

    # Palatals
    "च": "c", "छ": "ch", "ज": "j", "झ": "jh", "ञ": "ñ",

    # Retroflex
    "ट": "ṭ", "ठ": "ṭh", "ड": "ḍ", "ढ": "ḍh", "ण": "ṇ",

    # Dentals
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",

    # Labials
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",

    # Approximants
    "य": "y", "र": "r", "ल": "l", "व": "v",

    # Sibilants
    "श": "ś", "ष": "ṣ", "स": "s",

    # Others
    "ह": "h",
}

DEV_VOWELS = [
    "अ", "आ", "इ", "ई", "उ", "ऊ", "ऋ", "ॠ",
    "ए", "ऐ", "ओ", "औ"
]



def normalize_roman(text):
    text = text.lower().strip()
    text = re.sub(r"(.)\1{2,}", r"\1", text)
    text = re.sub(r"[–—-]+", " ", text)
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"\s+", " ", text)

    # Better Nepali romanization correction
    rules = {
        "cha ": "chha ",
        " ch ": " chh ",
        " x": " chh",
        "sh": "s",
        "sha": "sa",
    }

    for a, b in rules.items():
        text = text.replace(a, b)

    return text.strip()


def normalize_devanagari(t):
    t = t.strip()
    t = re.sub(r"[–—-]+", " ", t)
    t = re.sub(r"[,.]+", ",", t)
    t = re.sub(r"\s+", " ", t)
    return t




def is_valid_devanagari_word(word):
    """
    Checks:
    - Contains valid characters only
    - No illegal consonant clusters (e.g., ट्क, ञ्ग)
    - Proper use of matras
    """
    # Invalid English/ASCII presence
    if re.search(r"[a-zA-Z]", word):
        return False

    # Illegal clusters: retroflex + palatal (example rule)
    if re.search(r"[टठडढण][चछजझञ]", word):
        return False

    # Check for "्" virama rules
    if "्" in word:
        if word.endswith("्"):
            return False

    return True


def roman_matches_devanagari(roman, dev):
    """
    Checks if roman phonetic pattern matches the Devanagari shape.
    Example:
       roman 'khana' must contain 'kh'
       devanagari 'खाना' must contain ख
    """

    
    roman_clusters = re.findall(r"kh|gh|chh|ch|jh|ṭh|ḍh|ph|bh|[kgcjṭtdpbmnrlvsśṣhṅñṇ]", roman)

    
    dev_cons = [c for c in dev if c in DEV_CONSONANTS]

    
    if len(roman_clusters) != len(dev_cons):
        return False

    return True


def error_check_pair(roman, dev):
    """
    Returns list of issues found in a mapping.
    """
    issues = []

    if not is_valid_devanagari_word(dev):
        issues.append("Invalid Devanagari structure")

    if not roman_matches_devanagari(roman, dev):
        issues.append("Phonetic mismatch Roman→Dev")

    return issues



def load_dataset(path):
    pairs = []
    for line in open(path, "r", encoding="utf-8"):
        if "," not in line:
            continue

        roman, dev = line.split(",", 1)

        roman = normalize_roman(roman)
        dev = normalize_devanagari(dev)

        if roman and dev:
            pairs.append((roman, dev))

    return pairs


def deduplicate(pairs):
    rom_map = defaultdict(list)
    for r, d in pairs:
        rom_map[r].append(d)

    cleaned = []
    for r, devs in rom_map.items():
        best = max(devs, key=len)
        cleaned.append((r, best))

    return cleaned


def split_words(pairs):
    word_pairs = []
    misaligned = []
    errors = []

    for r, d in pairs:
        r_w = r.split()
        d_w = d.split()

        if len(r_w) != len(d_w):
            misaligned.append((r, d))
            continue

        for rw, dw in zip(r_w, d_w):
            issue_list = error_check_pair(rw, dw)
            if issue_list:
                errors.append((rw, dw, "; ".join(issue_list)))
            word_pairs.append((rw, dw))

    return word_pairs, misaligned, errors


def save_csv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerows(rows)


def main():
    raw = load_dataset("./TransliterateLL.txt")
    print(" → Raw pairs:", len(raw))

    cleaned = deduplicate(raw)
    print(" → Clean sentences:", len(cleaned))
    
    word_pairs, misaligned, errors = split_words(cleaned)

    save_csv("cleaned_sentences.csv", cleaned)
    save_csv("cleaned_word_pairs.csv", word_pairs)
    save_csv("pairs_needing_review.csv", misaligned)
    save_csv("phonetic_errors.csv", errors)



if __name__ == "__main__":
    main()
