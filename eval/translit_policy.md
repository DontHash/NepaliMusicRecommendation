# Transliteration policy (v1, legacy gold + review workflow)

Decision rubric for `eval/translit_gold_lines.csv` and
`eval/translit_gold_words.csv` — the reference sets behind
`scripts/check_transliteration.py`. It exists so the Roman -> Devanagari
transliterator is scored against a written standard instead of taste, and so
the teacher pass (track A1) has a target convention to imitate.

The gold sources are the legacy hand-authored pairs (`TransliterateLL.txt`,
`Data1.csv`..`Data4.csv`), which the current Aksharantar-trained checkpoint has
never seen. They are in-domain (song lines, real user-style romanization) and
therefore the only honest out-of-distribution signal available before the
teacher pass.

## Units

- One row per **distinct roman line** (`translit_gold_lines.csv`) or **distinct
  roman word** (`translit_gold_words.csv`). Repeats are collapsed at build time.
- Scoring is character-level: CER is Levenshtein distance divided by reference
  characters, micro-averaged over the set. Exact-match is the share of items
  equal to the reference.
- References are the *target* transliteration, not a normalization of the
  model's output.

## Rules

1. **Standard Nepali orthography wins.** Write the form a careful writer would
   use, as attested in the natively-Devanagari corpus (`script_style_original =
   devanagari`). `kaha` -> कहाँ, `kahi` -> कहीँ, `sanga` -> सँग, `aaja` -> आज,
   `door` -> दूर.
2. **The copula is छ.** Corpus-style `cha`, `chha` and `chh` all map to छ when
   they spell the verb (`huncha` -> हुन्छ, `garchu` -> गर्छु, `chau` -> छौ,
   `lauchau` -> लाउँछौं). `cha` is *not* चा; चा only appears inside words where
   the vowel is really आ (चा in `charcha` -> चर्चा).
3. **`v` before a vowel is भ in corpus spelling** (`vana` -> भन, `vanne` ->
   भन्ने, `bhana` -> भन). `b` stays ब (`bata` -> बाट). Do not "correct" the
   romanization in the reference: transliterate what is written.
4. **English stays Latin.** The gate (`lyrics_pipeline/transliterator.py`)
   keeps dictionary English and contraction tails untouched; the gold follows
   the same convention (`Ho no—no ना ना—ना—ना—ना`). Do not add Devanagari for
   English words, and do not add Latin for Nepali ones.
5. **Token boundaries are preserved.** The model is word-level: one roman token
   produces one Devanagari token. Compounds written as two words
   (`Timi prati` -> तिमी प्रति) stay two words in the reference even though
   तिमीप्रति is also correct Nepali; note the alternative in `notes`.
6. **Punctuation and dashes are copied through** from the roman line
   (`(बढ्दो छ)`, `ना—ना`). Devanagari danda is not introduced.
7. **Names use conventional Devanagari**: `bhisma` -> भीष्म, not भिस्मा.
8. **Variants**: where two spellings are both standard (बर्षा/वर्षा,
   यहाँ/यहां), the reference picks one and records the other in `notes`. The
   metric counts the other as an error; that is accepted noise.
9. **Out of scope**: grammar, word order, meaning, and sentence-level editing.
   The reference is a transliteration, not a translation.

## Exclusions

- Misaligned legacy rows (roman and gold are different text) — listed in
  `LINE_EXCLUSIONS` / `WORD_EXCLUSIONS` in `scripts/build_translit_gold.py`.
- English passthrough pairs (`yeah` -> `yeah`) and numeral conversions
  (`chaudha` -> १४): not transliteration.
- Single-character roman tokens (`m`, `j`, `k`): too ambiguous to score.
- Word pairs whose gold depends on context (`ma` -> म or मा, `pani` -> पनि or
  पानी). These are exported to `eval/translit_ambiguous_words.csv` for the
  context-rescoring work (A3) and are **not** scored context-free.

## Metrics and thresholds

`scripts/check_transliteration.py` writes
`music_rec_artifacts/transliteration_report.json` and fails when a metric
crosses its threshold (defaults in the script are the A0 baseline plus a small
margin):

| Metric | Model only (A0) | + lexicon (A2) | + context (A3) |
|---|---|---|---|
| Line CER | 0.1037 | 0.0915 | **0.0837** |
| Line exact-match | 9.6% | 14.9% | **18.8%** |
| Word CER | 0.1089 | 0.1030 | 0.1030 |
| Word exact-match | 65.0% | 68.0% | 68.0% |
| Gate cases | 4/4 | 4/4 | 4/4 |
| Lexicon validity | 84.3% | 84.8% | 84.6% |

The decode pipeline is layered, and each layer is switchable for A/B runs:

1. **English gate** — dictionary English and contraction tails stay Latin.
2. **Lexicon** (`lyrics_pipeline/translit_lexicon.py`, generated) — unambiguous
   roman tokens resolved by lookup; context-dependent tokens are excluded.
3. **Context resolver** (`lyrics_pipeline/context_resolver.py`, tables from
   `lyrics_pipeline/translit_context.py`) — ambiguous tokens pick their reading
   from left/right word bigrams over the Devanagari-origin corpus, with the
   teacher reading prior as backoff.
4. **Model** — everything else, plus the fallback when the tables miss.

Lexicon validity is the share of Devanagari tokens produced for real romanized
corpus songs that are attested in the natively-Devanagari part of the corpus.
It is a **lower bound**: valid words missing from the 1,421-song reference set
(e.g. खेलिरहेको) count as misses. Use it as a relative regression signal.

## Review workflow

1. `python scripts/build_translit_review.py` regenerates
   `eval/translit_review.csv` + `.md` with the model's current prediction and
   per-row CER. New candidate lines are **held out** from the teacher training
   set (`R_data/raw/gemini/translit_corpus_v1/labels.jsonl`), so gold v2 scores
   lines the system was never distilled from. Draft and human columns survive a
   rebuild.
2. `python scripts/draft_translit_review.py` fills `draft_devanagari` /
   `draft_cer` with a second model's opinion. The draft is an **aid, never a
   label**: it comes from the same model family as the teacher, and on the
   legacy gold it produced mixed-script output and untransliterated lines. It
   never sees the legacy label when drafting a gold row, so disagreements are
   genuine second opinions.
3. Review `eval/translit_review_quick.csv` (120 held-out lines with the draft
   pre-filled, plus the 37 legacy rows where the draft and the pipeline agree
   against the recorded label). Edit or delete what you disagree with; leave
   `user_devanagari` empty to keep the existing label. Accepting the draft
   blindly makes the gold a copy of the teacher — the point of the sheet is the
   human decision.
4. `python scripts/apply_translit_review.py` writes the accepted rows to
   `eval/translit_gold_v2.json`, which `scripts/build_translit_gold.py` merges
   on the next build. Rebuild and re-score:
   `python scripts/build_translit_gold.py && python scripts/check_transliteration.py`.

The legacy line gold keeps its original convention (editorial punctuation,
parenthetical repeats, compound spacing). Where that convention conflicts with
the modern pipeline, the disagreement is a style difference rather than an
error; gold v2 additions record the modern convention instead.
