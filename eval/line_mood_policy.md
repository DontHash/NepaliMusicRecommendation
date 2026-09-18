# Line mood policy (v2, agent-annotated on the rebuilt corpus)

Decision rubric for `eval/line_mood_gold.csv` — the line-level companion to the
song-level set in `eval/mood_gold.csv`. It exists so the probe's per-line
joy/sadness/anger picks can be audited and improved against a written standard,
not vibes.

v2 applies to the rebuilt corpus (C5): scrape artifacts were removed from the
lyric text before labeling, the quarantined legacy songs (1855 Aakashbandi,
1860 Katha) were dropped from the corpus and both gold sets (see
`eval/gold_exclusions.csv`), and English code-switch is preserved in Latin
script by the transliteration gate. Line texts therefore read as the model will
see them at inference time.

## Units

- One row per **distinct non-empty lyric line**; repeated refrains are labeled
  once (`occurrences` records how often the text repeats, `line_index` is the
  first occurrence, matching `music_rec.mood_attribution.line_spans`).
- Labels are **line-local**: read the line on its own. Song context may be used
  only to disambiguate an otherwise unreadable line — never to import the song's
  overall mood into a line that does not carry it.
- Label vocabulary: `joy`, `sadness`, `anger`, `neutral` (fear/depression are
  out of scope for the 3-emotion model; map to the nearest of these or neutral).
- Polarity is per line: `positive`, `negative`, `mixed`, `neutral`.

## Rules

1. **Explicit affect only for joy.** Joy requires an expressed positive state:
   happiness/joy words or their clear equivalents — `खुशी`, `आनन्द`, `मज्जा`,
   `उमङ्ग`, `रमाइलो`, smiling, celebration, gratitude/warmth (1938 Aama),
   festive bustle (3396). **Romance/devotion alone is neutral** (3235 lines 2-5;
   1365 `तिमी नै हाउ`), matching the song-level rule that "romantic devotion" is
   not joy (gold 263). Playful courtship/teasing **does** count as joy (1469,
   3396 register) because the playfulness itself is positive affect.
2. **National/cultural pride is not joy** unless happiness is expressed
   (3174 `म चाहिँ नेपाली` → neutral). Devotional hymns likewise (263).
3. **Sadness = grief, loss, longing, tears, pain, melancholy.** Covers explicit
   heartbreak (4024, 182), drinking-to-forget despair (2164), carried wounded
   heart (2252). A line describing the *infliction* with a named target leans
   anger (see 4).
4. **Anger = directed**. Accusation, protest, indictment, threat, curse, or
   confrontation aimed at someone/something: 3980 street defiance, 1511 "who
   set my heart on fire", 3174 caste critique, 3248 saw-on-wounded-heart.
   Undirected suffering stays sadness even inside anger songs (1511 "another
   heart weeping" → sadness). Bitter grief plus a blamed target → anger; the
   target decides.
5. **Comfort resolves pain.** If the line's own event is being comforted or the
   gratitude for it, label joy: 1938 `आँशु मेरो पुछि दियौ` (you wiped my tears →
   joy), `दुख मेरो बुझि दियौ` → joy; whereas lines that describe the pain itself
   (`कालो कालो रातमा`, `घाउमा पिडामा`) → sadness. This is deliberate: tears and
   sorrow words often appear in resolved, grateful lines and must not be read as
   sadness by keyword alone.
6. **Negation follows the speaker's stance, not the word.** 182
   `सम्झेर रुनु छैन` ("I mustn't cry again") → sadness (denied crying still
   evidences grief); 3235 `नहुनु है दु:खी` ("may you not be sad") → joy
   (blessing). Judge what the line commits to.
7. **Neutral** = facts, questions, vocatives, inventory/roll-calls, filler
   (`लैबरी`, hums), fragments, philosophical statements without affect. Neutral
   is the default when in doubt; it is not a failure label — 100/249 rows are
   neutral on purpose to measure the probe's false positives.
8. **Code-switch lines** are labeled by their English meaning, whether the
   English appears in Latin script (`Hey` vocatives, 1365) or embedded in
   Devanagari (`लभ`, `बेबी`). Rap lines that are English all the way through are
   labeled by what the English says.
9. **Scrape artifacts are excluded, not labeled.** The rebuilt corpus strips
   site footers, credit blocks, hashtags, and embeds before transliteration, so
   they no longer appear in the gold text. If a reviewer spots one, fix the
   cleaner and rebuild rather than labeling it; the `artifact` cue exists only
   as a legacy value.

## Columns

- `cue_type` — why the label holds: `lexical` (emotion word), `metaphor`
  (imagery), `negation`, `address` (plea/accusation to someone),
  `context_only` (needs song/world context), `repetition` (refrain/fragment),
  `code_switch`, `artifact` (legacy), `filler`, `none`.
- `difficulty` — `easy` (unambiguous), `medium` (needs the cue rules),
  `hard` (ambiguous/fragment; expected probe failures).
- `notes` — one-line justification, written for the error-analysis breakdown.
- `source` — `agent_v2` for this pass; corrections bump this.

## Deliberate asymmetries

- A song's lines need not average to its song-level gold primary (757 Asaar is
  joy/sadness by design; 263 is "none" while many lines are fond).
- Line labels are conservative; the review file (`eval/line_mood_review.csv`)
  carries the probe's current pick next to each label so disagreements, not
  just scores, drive the tuning in the follow-up.
