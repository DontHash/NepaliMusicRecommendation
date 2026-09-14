#!/usr/bin/env python3
"""Generate a small Roman -> Devanagari dictionary for the OrderFlow ordering
domain using the trained char transliterator.

The OrderFlow app is TypeScript/Next.js with no Python runtime in production.
This offline job builds a deterministic {roman: devanagari} JSON that is
committed to that repository for pure-TS lookup (0 ms, no ML runtime), while
still letting us update it whenever the transliterator checkpoint improves.

Usage:
  python scripts/export_ordering_dict.py \\
    --checkpoint char_transformer_442.pt --vocab char_vocab.pkl \\
    --output nepali_ordering_dict.json
  # Optional: fold in the romanized names of a real menu as extra keys
  python scripts/export_ordering_dict.py --menu menu.json --output out.json

Entries are normalized to NFKC lowercase and transliterated word-by-word
(matches how TypeScript will tokenize customer input). Non-Latin input is
passed through unchanged.
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lyrics_pipeline.transliterator import NepaliTransliterator  # noqa: E402

# Curated Romanized-Nepali ordering vocabulary. Words/phrases are lowercased
# by the exporter; English borrowings ("delivery", "order") are fine to keep
# because the app already matches them directly and the Devanagari forms help
# alias matching against menu items written in Devanagari.
DOMAIN_WORDS = [    # Food / menu
    "momo", "momos", "buff momo", "buff", "chicken momo", "vegetable momo",
    "veg momo", "jhol", "kothey", "steamed", "fried", "steam momo",
    "chowmein", "chow mein", "noodles", "thakali", "thakali set", "thali",
    "sekuwa", "chicken sekuwa", "roti", "rice", "bhat", "dal", "tarkari",
    "saag", "achar", "gundruk", "dhido", "machha", "khasi",
    "masala tea", "chia", "chiya", "tea", "coffee", "milk tea", "sweet lassi",
    "lassi", "water", "pani", "mineral water",
    # Ordering / checkout
    "order", "orders", "delivery", "pickup", "pick up", "takeaway",
    "address", "thegana", "name", "naam", "confirm", "confirmation",
    "cancel", "cancelled", "bill", "payment", "instructions", "note", "notes",
    "yes", "no", "ok", "okay", "please", "dhanyabad", "thank you", "thanks",
    "hello", "hi", "namaste", "bye",
    # Questions / quantities
    "kati", "how much", "price", "rate", "menu", "available", "unavailable",
    "kati samma", "wait", "ek", "dui", "tin", "char", "paanch", "chha",
    "sat", "aath", "nau", "das",
    # Common filler / politeness
    "khana", "khanu", "hajur", "la", "ho", "chan", "hoina", "ma", "parcha",
    "parchha", "paisa", "rupee", "rupaiya",
]


def normalize(word: str) -> str:
    return unicodedata.normalize("NFKC", word.strip().lower())


# High-certainty canonical Devanagari for common ordering terms (aligned with
# the demo menu aliases). Tuned by a human; wins over the model's noisy output.
# Model output is used only as a fallback for words not listed here.
OVERRIDES = {
    "momo": "मम", "momos": "मम", "buff momo": "बफ मम", "buff momos": "बफ मम",
    "chicken momo": "चिकन मम", "chicken momos": "चिकन मम",
    "vegetable momo": "तरकारी मम", "veg momo": "तरकारी मम",
    "jhol": "झोल", "kothey": "कोथे", "steamed": "उसिनेको", "fried": "तारेको",
    "steam momo": "उसिनेको मम",
    "chowmein": "चाउमिन", "chow mein": "चाउमिन", "noodles": "चाउमिन",
    "thakali": "थकाली", "thakali set": "थकाली सेट", "thali": "थाली",
    "sekuwa": "सेकुवा", "chicken sekuwa": "चिकन सेकुवा",
    "roti": "रोटी", "rice": "चामल", "bhat": "भात", "dal": "दाल",
    "tarkari": "तरकारी", "saag": "साग", "achar": "अचार", "gundruk": "गुन्द्रुक",
    "dhido": "ढिडो", "machha": "माछा", "khasi": "खसी",
    "masala tea": "मसला चिया", "chia": "चिया", "chiya": "चिया",
    "tea": "चिया", "coffee": "कफी", "milk tea": "दूध चिया",
    "sweet lassi": "मीठो लस्सी", "lassi": "लस्सी",
    "water": "पानी", "pani": "पानी", "mineral water": "मिनरल वाटर",
    "order": "अर्डर", "orders": "अर्डरहरू", "delivery": "डेलिभरी",
    "pickup": "पिकअप", "pick up": "पिकअप", "takeaway": "टेकअवे",
    "address": "ठेगाना", "thegana": "ठेगाना", "name": "नाम", "naam": "नाम",
    "confirm": "पुष्टि", "confirmation": "पुष्टि", "cancel": "रद्द",
    "cancelled": "रद्द", "bill": "बिल", "payment": "भुक्तानी",
    "instructions": "निर्देशन", "note": "नोट", "notes": "नोटहरू",
    "yes": "हो", "no": "होइन", "ok": "हुन्छ", "okay": "हुन्छ",
    "please": "कृपया", "dhanyabad": "धन्यवाद", "thank you": "धन्यवाद",
    "thanks": "धन्यवाद", "hello": "नमस्ते", "hi": "नमस्ते", "namaste": "नमस्ते",
    "bye": "बिदा", "kati": "कति", "how much": "कति", "price": "मूल्य",
    "rate": "दर", "menu": "मेनु", "available": "उपलब्ध", "unavailable": "अनुपलब्ध",
    "kati samma": "कति सम्म", "wait": "पर्खनुहोस्",
    "ek": "एक", "dui": "दुई", "tin": "तीन", "char": "चार", "paanch": "पाँच",
    "chha": "छ", "sat": "सात", "aath": "आठ", "nau": "नौ", "das": "दस",
    "khana": "खाना", "khanu": "खानु", "hajur": "हजुर", "la": "ल",
    "ho": "हो", "chan": "छन्", "hoina": "होइन", "ma": "म", "parcha": "पर्छ",
    "parchha": "पर्छ", "paisa": "पैसा", "rupee": "रुपैयाँ", "rupaiya": "रुपैयाँ",
}


def build_dict(tr: NepaliTransliterator, words: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for phrase in words:
        key = normalize(phrase)
        if not key:
            continue
        tokens = key.split()
        parts: list[str] = []
        changed = False
        for token in tokens:
            index_key = " ".join(tokens)
            canonical = token
            if index_key in OVERRIDES and len(tokens) == 1:
                canonical = OVERRIDES[index_key]
            elif token in OVERRIDES:
                canonical = OVERRIDES[token]
            else:
                devanagari = tr.transliterate_word(token)
                canonical = devanagari if devanagari and devanagari != token else token
            parts.append(canonical)
            if canonical != token:
                changed = True
        if changed:
            out[key] = " ".join(parts)
    return out


def load_menu_words(menu_path: Path | None) -> list[str]:
    if not menu_path:
        return []
    data = json.loads(menu_path.read_text(encoding="utf-8"))
    items = data.get("items") if isinstance(data, dict) else data
    words: list[str] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        for field in ("name", "category"):
            value = item.get(field)
            if isinstance(value, str) and value.strip():
                words.append(value)
        aliases = item.get("aliases")
        if isinstance(aliases, list):
            words.extend(alias for alias in aliases if isinstance(alias, str))
    return words


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    default_checkpoint = ROOT / "char_transformer_442.pt"
    default_vocab = ROOT / "char_vocab.pkl"
    parser.add_argument("--checkpoint", type=Path, default=default_checkpoint,
                        help="Transliteration checkpoint (.pt)")
    parser.add_argument("--vocab", type=Path, default=default_vocab,
                        help="Vocabulary pickle (.pkl)")
    parser.add_argument("--menu", type=Path, default=None,
                        help="Optional menu JSON {items:[{name, category, aliases}]} to fold in")
    parser.add_argument("--output", type=Path, required=True,
                        help="Output JSON path")
    args = parser.parse_args()

    if not args.checkpoint.exists():
        sys.exit(f"Checkpoint not found: {args.checkpoint}")
    if not args.vocab.exists():
        sys.exit(f"Vocabulary not found: {args.vocab}")

    tr = NepaliTransliterator(
        checkpoint_path=args.checkpoint,
        vocab_path=args.vocab,
        decode="greedy",
        device="cpu",
    )
    if not tr.available:
        sys.exit("Transliterator failed to load (is torch available?).")

    words = list(DOMAIN_WORDS) + load_menu_words(args.menu)
    result = build_dict(tr, words)
    result = dict(sorted(result.items()))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(result)} entries to {args.output}")
    for key in list(result)[:15]:
        print(f"  {key} -> {result[key]}")


if __name__ == "__main__":
    main()
