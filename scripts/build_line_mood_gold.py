"""Build eval/line_mood_gold.csv from hand-authored line labels.

Labels are keyed by song and follow the order of first occurrence of distinct
non-empty lines (see eval/line_mood_policy.md for the decision rubric). The
builder expands each distinct text to its first line_index and records how many
times it occurs, so repeated refrains are labeled once and stay consistent.

Usage:
    python scripts/build_line_mood_gold.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from music_rec.mood_attribution import line_spans

OUT_CSV = PROJECT_ROOT / "eval" / "line_mood_gold.csv"
SOURCE = "agent_v1"

LABELS: dict[int, list[tuple[str, str, str, str, str]]] = {
    3235: [
        ("joy", "positive", "lexical", "easy", "explicit happiness blessing (खुशी)"),
        ("joy", "positive", "negation", "medium", "blessing against sorrow (नहुनु दु:खी)"),
        ("neutral", "positive", "context_only", "medium", "devotion imagery; no happiness"),
        ("neutral", "positive", "context_only", "medium", "devotion; no happiness"),
        ("neutral", "positive", "context_only", "medium", "togetherness wish; no happiness"),
        ("neutral", "positive", "context_only", "medium", "love-world wish; no happiness"),
    ],
    3396: [
        ("neutral", "neutral", "artifact", "easy", "scrape artifact header"),
        ("joy", "positive", "lexical", "easy", "festive eat-drink cheer"),
        ("joy", "positive", "lexical", "easy", "new clothes, swing fun"),
        ("joy", "positive", "lexical", "easy", "उमङ्ग excitement"),
        ("joy", "positive", "lexical", "easy", "खुशीयाली explicit"),
        ("joy", "positive", "lexical", "easy", "मज्जा kite fun"),
        ("joy", "positive", "context_only", "medium", "ritual celebration"),
        ("neutral", "neutral", "none", "easy", "factual festival line"),
        ("joy", "positive", "context_only", "medium", "family gathering warmth"),
        ("joy", "positive", "lexical", "easy", "dance-sing रमाइलो"),
        ("joy", "positive", "lexical", "easy", "रमाइलो refrain"),
        ("joy", "positive", "context_only", "medium", "reunion happiness"),
        ("sadness", "negative", "context_only", "hard", "left-behind ache; bittersweet"),
        ("joy", "positive", "context_only", "medium", "reunion happiness"),
        ("sadness", "mixed", "context_only", "medium", "homesick remembrance"),
        ("joy", "positive", "context_only", "medium", "consoling celebration"),
        ("joy", "positive", "context_only", "medium", "celebrate together"),
        ("joy", "positive", "lexical", "easy", "रमाइलो run-on refrain"),
        ("joy", "positive", "lexical", "medium", "fun line; junk suffix नएम्बेड"),
    ],
    1938: [
        ("joy", "positive", "context_only", "medium", "precious-life gratitude"),
        ("joy", "positive", "lexical", "medium", "gift of life gratitude"),
        ("joy", "positive", "context_only", "medium", "pure gift gratitude"),
        ("joy", "positive", "context_only", "medium", "symbol of love gratitude"),
        ("joy", "positive", "context_only", "medium", "warm-lap warmth"),
        ("joy", "positive", "context_only", "medium", "dreams under her care"),
        ("joy", "positive", "context_only", "medium", "holding hands warmth"),
        ("neutral", "neutral", "none", "medium", "paths walked; factual"),
        ("neutral", "positive", "context_only", "medium", "adoration; no happiness"),
        ("neutral", "positive", "context_only", "medium", "adoration; no happiness"),
        ("neutral", "neutral", "repetition", "easy", "vocative refrain"),
        ("neutral", "positive", "context_only", "medium", "praised likeness"),
        ("neutral", "positive", "context_only", "medium", "angel praise"),
        ("joy", "positive", "context_only", "medium", "grateful for sacrifice"),
        ("joy", "positive", "context_only", "medium", "pure-love gratitude"),
        ("sadness", "negative", "metaphor", "medium", "dark-night suffering imagery"),
        ("sadness", "negative", "lexical", "medium", "hurtful-blow suffering"),
        ("joy", "positive", "context_only", "medium", "comforted; being held"),
        ("sadness", "negative", "lexical", "medium", "wounds and stinging pain"),
        ("joy", "positive", "lexical", "medium", "smile for her"),
        ("neutral", "positive", "context_only", "medium", "live-for-you devotion"),
        ("joy", "positive", "context_only", "medium", "tears wiped; comfort"),
        ("joy", "positive", "context_only", "medium", "sorrow understood; comfort"),
        ("joy", "positive", "lexical", "medium", "wished happiness (सुख)"),
        ("joy", "positive", "context_only", "medium", "shown the way; gratitude"),
        ("joy", "positive", "metaphor", "medium", "lit my lamp"),
        ("joy", "positive", "metaphor", "medium", "made life bright"),
        ("neutral", "neutral", "repetition", "easy", "vocative refrain"),
    ],
    1469: [
        ("joy", "positive", "address", "medium", "playful address; flirtation"),
        ("neutral", "neutral", "context_only", "medium", "teasing risk of attachment"),
        ("neutral", "mixed", "metaphor", "hard", "playful dying hyperbole; ambiguous"),
        ("neutral", "neutral", "context_only", "hard", "folk banter; unclear"),
        ("neutral", "neutral", "context_only", "medium", "river-valley scenery"),
        ("neutral", "positive", "context_only", "medium", "love-in-heart; no happiness"),
        ("neutral", "neutral", "context_only", "medium", "eyes-liner flirt image"),
        ("neutral", "positive", "context_only", "medium", "teasing invitation"),
        ("neutral", "mixed", "metaphor", "hard", "repeated dying hyperbole"),
        ("neutral", "neutral", "repetition", "medium", "folk refrain"),
        ("neutral", "neutral", "context_only", "medium", "red-blouse teasing image"),
        ("neutral", "positive", "context_only", "medium", "love glowing on face"),
        ("neutral", "neutral", "metaphor", "medium", "folk garden image"),
        ("sadness", "negative", "address", "medium", "weeping-wait plea (tears)"),
        ("neutral", "neutral", "context_only", "hard", "folk refrain fragment"),
    ],
    4024: [
        ("neutral", "mixed", "context_only", "medium", "devotion odyssey; mixed"),
        ("sadness", "negative", "address", "medium", "don't-ignore plea"),
        ("sadness", "negative", "address", "medium", "stay-a-moment plea"),
        ("sadness", "mixed", "context_only", "medium", "memories need no love; wistful"),
        ("sadness", "negative", "metaphor", "medium", "heart keeps searching"),
        ("sadness", "negative", "context_only", "medium", "self-blame"),
        ("sadness", "negative", "address", "easy", "don't-leave plea"),
        ("sadness", "negative", "address", "easy", "don't-break-heart plea"),
        ("sadness", "negative", "address", "medium", "cruel-one plea; accusatory"),
        ("sadness", "negative", "lexical", "easy", "heart hurts"),
        ("sadness", "negative", "lexical", "medium", "sudden departure"),
        ("neutral", "mixed", "context_only", "medium", "devotion odyssey variant"),
    ],
    182: [
        ("sadness", "negative", "context_only", "medium", "words unsaid; unheard"),
        ("sadness", "negative", "lexical", "easy", "heavy heart, left behind"),
        ("sadness", "negative", "context_only", "medium", "false promises; grief-toned"),
        ("sadness", "negative", "lexical", "medium", "incomplete bond; parting"),
        ("sadness", "negative", "context_only", "medium", "bittersweet warning"),
        ("sadness", "negative", "lexical", "easy", "heart hurts in love"),
        ("sadness", "negative", "context_only", "medium", "don't-return warning"),
        ("sadness", "negative", "lexical", "easy", "trust lost"),
        ("sadness", "negative", "address", "easy", "don't come even in dreams"),
        ("sadness", "negative", "negation", "medium", "mustn't cry (रुनु छैन)"),
        ("sadness", "negative", "address", "medium", "don't give memories"),
        ("neutral", "mixed", "context_only", "medium", "farewell well-wishing"),
        ("neutral", "mixed", "context_only", "medium", "write your own story"),
        ("sadness", "mixed", "address", "medium", "forget-me plea"),
        ("neutral", "positive", "context_only", "medium", "well-wish"),
        ("sadness", "mixed", "context_only", "medium", "only wish: togetherness"),
        ("sadness", "mixed", "repetition", "medium", "togetherness refrain"),
        ("sadness", "negative", "context_only", "medium", "only memory remains"),
        ("neutral", "neutral", "filler", "easy", "humming"),
    ],
    2164: [
        ("sadness", "negative", "context_only", "medium", "evening drunkenness"),
        ("sadness", "negative", "context_only", "medium", "life distressed"),
        ("sadness", "negative", "repetition", "medium", "every-evening refrain"),
        ("sadness", "negative", "context_only", "medium", "helpless drinking"),
        ("sadness", "mixed", "lexical", "medium", "drank in sorrow and joy; escapism"),
        ("sadness", "negative", "context_only", "medium", "self-destructive pledge"),
        ("sadness", "negative", "lexical", "medium", "life shortening"),
        ("sadness", "negative", "lexical", "medium", "life distressed refrain"),
        ("sadness", "negative", "metaphor", "medium", "temple vs cremation drinking"),
        ("sadness", "mixed", "context_only", "hard", "forced gaiety; escapism"),
        ("sadness", "negative", "lexical", "easy", "crying alone (रुदै)"),
        ("sadness", "negative", "context_only", "medium", "nightly intoxication"),
    ],
    1860: [
        ("neutral", "neutral", "none", "easy", "story narration"),
        ("neutral", "neutral", "none", "hard", "corrupt OCR line"),
        ("neutral", "neutral", "none", "hard", "corrupt OCR; love subject"),
        ("neutral", "neutral", "none", "hard", "was their world"),
        ("sadness", "negative", "metaphor", "hard", "fire destroying world; OCR"),
        ("neutral", "neutral", "context_only", "hard", "desired star; setup"),
        ("neutral", "neutral", "none", "hard", "corrupt OCR"),
        ("sadness", "negative", "context_only", "hard", "hopes ended"),
        ("neutral", "neutral", "none", "hard", "corrupt OCR future line"),
        ("joy", "positive", "context_only", "hard", "hopeful happy times; later dashed"),
        ("sadness", "negative", "lexical", "hard", "trapped enduring atrocity"),
        ("sadness", "negative", "context_only", "hard", "fear of society"),
        ("sadness", "negative", "context_only", "hard", "fleeing in distress"),
        ("joy", "positive", "context_only", "hard", "dreaming joy for love"),
        ("sadness", "negative", "context_only", "hard", "foreboding fate"),
        ("sadness", "negative", "context_only", "hard", "sweet moments never came"),
        ("sadness", "negative", "context_only", "hard", "time passed; love wanting"),
        ("sadness", "negative", "context_only", "hard", "no sign of change"),
        ("sadness", "negative", "metaphor", "hard", "black page of betrayal"),
        ("sadness", "negative", "context_only", "hard", "helpless; unheard cries"),
        ("sadness", "negative", "lexical", "hard", "heart pain unsoothed"),
        ("sadness", "negative", "metaphor", "hard", "living corpse; wounds"),
        ("sadness", "negative", "metaphor", "hard", "who brings her happiness"),
    ],
    3980: [
        ("anger", "negative", "context_only", "medium", "injustice of good works"),
        ("neutral", "neutral", "context_only", "medium", "self-assertion; defiant"),
        ("anger", "negative", "metaphor", "medium", "violence imagery; blood boils"),
        ("neutral", "neutral", "context_only", "medium", "street origin story"),
        ("neutral", "mixed", "context_only", "medium", "took own path; defiant"),
        ("neutral", "negative", "context_only", "medium", "wanted; press coverage"),
        ("neutral", "neutral", "none", "easy", "didn't care"),
        ("neutral", "neutral", "none", "easy", "don't watch news"),
        ("anger", "negative", "address", "medium", "encounter threat; beware"),
        ("anger", "negative", "address", "medium", "respect-or-else threat"),
        ("neutral", "negative", "context_only", "medium", "gang boast"),
        ("neutral", "mixed", "context_only", "medium", "defiant contrast"),
        ("anger", "negative", "context_only", "medium", "accusation of fakeness"),
        ("neutral", "neutral", "none", "easy", "ethnic roll call"),
        ("anger", "negative", "address", "medium", "refuse jail; defiant"),
        ("anger", "negative", "context_only", "medium", "resentment of politics"),
        ("anger", "negative", "address", "medium", "put-yourself-there taunt"),
        ("anger", "negative", "address", "medium", "challenge question"),
        ("anger", "negative", "address", "medium", "jail threat"),
    ],
    1511: [
        ("anger", "negative", "metaphor", "medium", "who set my heart on fire"),
        ("anger", "negative", "metaphor", "medium", "accusatory; tears as injury"),
        ("anger", "negative", "metaphor", "hard", "curse: fire inside you"),
        ("anger", "negative", "metaphor", "hard", "curse: heart burns longing"),
        ("anger", "negative", "metaphor", "hard", "knife-edge betrayal image"),
        ("anger", "negative", "context_only", "medium", "love shifted; mocked"),
        ("anger", "negative", "context_only", "medium", "love shifted; mocked variant"),
        ("anger", "negative", "metaphor", "medium", "grinding on stone laughing"),
        ("anger", "negative", "metaphor", "hard", "life as wildfire"),
        ("anger", "negative", "context_only", "hard", "burdened the meeting heart"),
        ("anger", "negative", "context_only", "medium", "lifetime of tears; blame"),
        ("sadness", "negative", "metaphor", "hard", "another heart weeping (grief)"),
        ("anger", "negative", "metaphor", "hard", "curse: may you drift"),
        ("anger", "negative", "metaphor", "medium", "who made my heart weep"),
    ],
    3174: [
        ("anger", "negative", "context_only", "medium", "why divided? indictment"),
        ("anger", "negative", "context_only", "medium", "caste entanglement critique"),
        ("neutral", "neutral", "context_only", "medium", "world uniting; setup"),
        ("anger", "negative", "address", "medium", "caste-question indictment"),
        ("anger", "negative", "address", "medium", "caste-question indictment"),
        ("anger", "negative", "context_only", "medium", "everyone wants a kingdom?"),
        ("anger", "negative", "context_only", "medium", "caste labels questioned"),
        ("anger", "negative", "context_only", "medium", "are we not the same?"),
        ("anger", "negative", "context_only", "medium", "to those who divide"),
        ("neutral", "neutral", "address", "medium", "say this; injunction"),
        ("neutral", "negative", "context_only", "medium", "don't know who you are"),
        ("neutral", "positive", "context_only", "medium", "Nepali identity assertion"),
        ("anger", "negative", "context_only", "medium", "caste critique"),
        ("neutral", "positive", "context_only", "easy", "heart is greatest"),
        ("sadness", "mixed", "context_only", "medium", "cynical regret of society"),
        ("anger", "negative", "context_only", "medium", "satire: whose Everest?"),
        ("anger", "negative", "context_only", "medium", "satire: dividing Buddha"),
        ("neutral", "positive", "context_only", "easy", "dear Nepal address"),
        ("neutral", "mixed", "context_only", "medium", "violence no longer wanted"),
    ],
    3248: [
        ("anger", "negative", "metaphor", "medium", "saw-on-wounded-heart accusation"),
        ("anger", "negative", "context_only", "medium", "what a game played on me"),
        ("neutral", "neutral", "context_only", "hard", "fragment; my own kin"),
        ("anger", "negative", "context_only", "hard", "state kills; corrupt line"),
        ("anger", "negative", "metaphor", "medium", "cruel murderous gaze"),
        ("neutral", "neutral", "context_only", "hard", "fragment; my own kin"),
        ("anger", "negative", "metaphor", "medium", "saw on wounded heart"),
        ("neutral", "neutral", "context_only", "hard", "fragment; my own kin"),
        ("sadness", "mixed", "metaphor", "hard", "dried springs lament; corrupt"),
        ("anger", "negative", "context_only", "medium", "what law applied? grievance"),
        ("anger", "negative", "context_only", "medium", "gossiped everywhere"),
        ("anger", "negative", "context_only", "medium", "slogans against me; why"),
        ("anger", "negative", "context_only", "hard", "sarcastic king-in-heart"),
        ("anger", "negative", "metaphor", "medium", "you struck the star"),
        ("neutral", "neutral", "artifact", "easy", "scrape artifact"),
        ("neutral", "neutral", "artifact", "easy", "scrape artifact"),
        ("neutral", "neutral", "artifact", "easy", "scrape artifact"),
        ("neutral", "neutral", "artifact", "easy", "scrape artifact"),
    ],
    757: [
        ("joy", "positive", "lexical", "medium", "rain joy imagery (सरर)"),
        ("joy", "positive", "lexical", "easy", "आनन्द explicit"),
        ("joy", "mixed", "context_only", "medium", "sorrow turned to dream"),
        ("sadness", "negative", "context_only", "medium", "life passed quickly; lament"),
        ("joy", "positive", "context_only", "medium", "city-soaked rain joy"),
        ("joy", "positive", "context_only", "medium", "monsoon return; delight"),
        ("neutral", "mixed", "context_only", "medium", "sun-and-rain philosophy"),
        ("neutral", "positive", "context_only", "medium", "love is greatest"),
        ("joy", "positive", "context_only", "medium", "blue sky delight"),
        ("joy", "positive", "context_only", "medium", "fog cleared; relief"),
        ("neutral", "positive", "context_only", "medium", "keeping heart true"),
        ("neutral", "positive", "context_only", "medium", "living on your support"),
        ("joy", "positive", "context_only", "medium", "streams flowing; rain joy"),
        ("neutral", "positive", "context_only", "medium", "returned to you; devotion"),
        ("sadness", "negative", "context_only", "medium", "life passed quickly variant"),
        ("joy", "positive", "context_only", "medium", "city-soaked rain variant"),
        ("joy", "positive", "context_only", "medium", "monsoon return variant"),
        ("neutral", "neutral", "filler", "easy", "लैबरी filler refrain"),
    ],
    2252: [
        ("sadness", "negative", "context_only", "medium", "remembrance self-loss"),
        ("sadness", "negative", "context_only", "medium", "alone together; longing"),
        ("sadness", "negative", "metaphor", "medium", "restless like waves"),
        ("sadness", "negative", "metaphor", "easy", "teardrops falling"),
        ("sadness", "negative", "metaphor", "medium", "flower dying daily"),
        ("sadness", "negative", "metaphor", "medium", "stone statue at crossroads"),
        ("sadness", "negative", "metaphor", "easy", "wounded heart carried"),
    ],
    263: [
        ("neutral", "mixed", "context_only", "medium", "name blown away; conceit"),
        ("neutral", "positive", "context_only", "easy", "name on moon; devotion"),
        ("neutral", "mixed", "context_only", "medium", "eclipse covers it"),
        ("neutral", "positive", "context_only", "easy", "name in heart"),
        ("neutral", "positive", "context_only", "medium", "love flourished?"),
        ("neutral", "positive", "context_only", "medium", "if called mad, so be it"),
        ("neutral", "positive", "context_only", "medium", "if called ascetic, so be it"),
        ("neutral", "positive", "context_only", "easy", "I am a lover"),
        ("neutral", "positive", "context_only", "medium", "love's priest?"),
        ("neutral", "positive", "context_only", "easy", "name on flower"),
        ("neutral", "mixed", "context_only", "medium", "bee takes the mark"),
        ("neutral", "positive", "context_only", "easy", "name on leaf"),
        ("neutral", "mixed", "context_only", "medium", "water washed it"),
        ("neutral", "positive", "context_only", "medium", "echoes in melody"),
        ("neutral", "mixed", "context_only", "hard", "दुःख idiom; ambiguous"),
        ("sadness", "mixed", "context_only", "medium", "no happiness without you"),
        ("neutral", "positive", "context_only", "medium", "always in your memory"),
        ("sadness", "negative", "context_only", "medium", "if separated in love"),
        ("neutral", "positive", "context_only", "easy", "name on Himalaya"),
        ("neutral", "mixed", "context_only", "medium", "snow melted together"),
        ("neutral", "positive", "context_only", "easy", "name on shore"),
        ("neutral", "mixed", "context_only", "medium", "waves washed away"),
        ("neutral", "positive", "context_only", "easy", "name in heart"),
        ("neutral", "positive", "context_only", "medium", "heartbeat image"),
    ],
    2061: [
        ("neutral", "neutral", "context_only", "hard", "corrupt OCR line"),
        ("neutral", "neutral", "context_only", "hard", "corrupt OCR line"),
        ("neutral", "positive", "address", "easy", "my love, my love"),
        ("neutral", "neutral", "context_only", "medium", "whose love? questioning"),
        ("neutral", "neutral", "context_only", "medium", "what memory came"),
        ("neutral", "neutral", "context_only", "medium", "what to call you"),
        ("neutral", "neutral", "repetition", "easy", "वनिदेउ filler"),
    ],
    1365: [
        ("neutral", "positive", "context_only", "medium", "gift picture to lovers"),
        ("neutral", "neutral", "context_only", "hard", "corrupt line"),
        ("neutral", "mixed", "context_only", "hard", "moments captured; philosophical"),
        ("neutral", "positive", "context_only", "medium", "your dear person; devotion"),
        ("neutral", "positive", "context_only", "medium", "what else a lover needs"),
        ("neutral", "positive", "context_only", "easy", "it's you; devotion"),
        ("neutral", "positive", "context_only", "easy", "one who loves me"),
        ("neutral", "positive", "context_only", "easy", "it's you refrain"),
        ("joy", "positive", "lexical", "easy", "gives me happiness (खुशी)"),
        ("neutral", "positive", "address", "medium", "hold this hand"),
        ("neutral", "positive", "context_only", "medium", "wish bond unbroken"),
        ("neutral", "neutral", "context_only", "medium", "let them see/hear"),
        ("neutral", "neutral", "context_only", "medium", "this relationship"),
        ("joy", "positive", "context_only", "medium", "no regret; contentment"),
        ("joy", "positive", "lexical", "medium", "we want happiness"),
        ("neutral", "mixed", "context_only", "medium", "let them talk; resolve"),
        ("neutral", "neutral", "context_only", "medium", "talk about us"),
        ("neutral", "neutral", "context_only", "medium", "whatever my caste"),
        ("neutral", "positive", "context_only", "easy", "it's you fragment"),
    ],
    1855: [
        ("neutral", "neutral", "context_only", "medium", "people circling own world"),
        ("neutral", "neutral", "context_only", "hard", "corrupt line; own world"),
        ("neutral", "neutral", "code_switch", "hard", "English; wake-up threat"),
        ("neutral", "neutral", "code_switch", "hard", "English; pivotal mind"),
        ("neutral", "neutral", "code_switch", "hard", "English; plans to stay up"),
        ("neutral", "neutral", "code_switch", "easy", "English; 1 AM bed"),
        ("neutral", "neutral", "code_switch", "hard", "English; nightly owl"),
        ("neutral", "mixed", "code_switch", "hard", "English; disturbing vibe"),
        ("sadness", "negative", "code_switch", "medium", "English: saddening explicit"),
        ("neutral", "neutral", "code_switch", "hard", "English; transcended"),
        ("joy", "positive", "code_switch", "medium", "English: bliss explicit"),
        ("neutral", "negative", "code_switch", "hard", "English; survival struggle"),
        ("anger", "negative", "code_switch", "medium", "English: release the monster"),
        ("joy", "positive", "code_switch", "medium", "English: radiating positivity"),
        ("neutral", "negative", "code_switch", "hard", "English; honest now"),
        ("neutral", "neutral", "context_only", "hard", "played small games"),
        ("neutral", "neutral", "context_only", "hard", "couldn't grow big"),
        ("sadness", "mixed", "context_only", "hard", "regret of not achieving"),
        ("neutral", "neutral", "filler", "easy", "vocal filler"),
        ("neutral", "neutral", "filler", "easy", "vocal filler"),
        ("neutral", "neutral", "filler", "easy", "vocal filler"),
    ],
}

EMOTIONS = {"joy", "sadness", "anger", "neutral"}
POLARITIES = {"positive", "negative", "mixed", "neutral"}
CUES = {
    "lexical",
    "metaphor",
    "negation",
    "address",
    "context_only",
    "repetition",
    "code_switch",
    "artifact",
    "filler",
    "none",
}
DIFFICULTIES = {"easy", "medium", "hard"}


def build() -> pd.DataFrame:
    corpus = pd.read_csv(PROJECT_ROOT / "music_rec_artifacts" / "cleaned_lyrics.csv", encoding="utf-8")
    corpus = corpus.fillna("").set_index("song_id")
    rows: list[dict] = []
    for song_id, labels in LABELS.items():
        text = str(corpus.loc[song_id, "lyrics"])
        spans = line_spans(text)
        groups: dict[str, list[int]] = {}
        order: list[str] = []
        for index, (start, end) in enumerate(spans):
            line = text[start:end]
            if line not in groups:
                groups[line] = []
                order.append(line)
            groups[line].append(index)
        if len(order) != len(labels):
            raise ValueError(
                f"song {song_id}: {len(order)} distinct lines but {len(labels)} labels"
            )
        for line, label in zip(order, labels):
            emotion, polarity, cue, difficulty, note = label
            if emotion not in EMOTIONS or polarity not in POLARITIES:
                raise ValueError(f"song {song_id}: bad label {emotion}/{polarity}")
            if cue not in CUES or difficulty not in DIFFICULTIES:
                raise ValueError(f"song {song_id}: bad cue/difficulty {cue}/{difficulty}")
            rows.append(
                {
                    "song_id": song_id,
                    "title": str(corpus.loc[song_id, "title"]),
                    "artist": str(corpus.loc[song_id, "artist"]),
                    "line_index": groups[line][0],
                    "text": line,
                    "occurrences": len(groups[line]),
                    "primary_emotion": emotion,
                    "polarity": polarity,
                    "cue_type": cue,
                    "difficulty": difficulty,
                    "notes": note,
                    "source": SOURCE,
                }
            )
    frame = pd.DataFrame(rows).sort_values(["song_id", "line_index"]).reset_index(drop=True)
    frame.to_csv(OUT_CSV, index=False, encoding="utf-8")
    return frame


if __name__ == "__main__":
    frame = build()
    counts = frame["primary_emotion"].value_counts().to_dict()
    print(f"wrote {len(frame)} labeled distinct lines -> {OUT_CSV}")
    print(f"emotion counts: {counts}")
    print(f"difficulty: {frame['difficulty'].value_counts().to_dict()}")
    print(f"songs: {frame['song_id'].nunique()}")
