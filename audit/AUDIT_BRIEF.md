# ProjectR Audit Brief (shared context for all audit tracks)

## What ProjectR is

A **Nepali music intelligence system built on lyrics only** (no audio). End-to-end:

1. **Corpus collection** (`data_collection/`): resumable API-first collector — SQLite WAL work queue, cached HTTP with retries/rate limits/circuit breaker, site crawlers (sitemaps/pagination), LRCLIB/iTunes/Deezer harvest, compaction to `R_data/corpus/corpus_raw.csv`. Seed artists enumerate ~27k candidates; ~4.2k songs fetched.
2. **Cleaning + transliteration** (`lyrics_pipeline/`): regex/pattern cleaner stripping site junk, English gate, custom char-level Transformer transliterator (Roman→Devanagari, ~4M params, ~3.5% CER Aksharantar, 7.47% line CER in-domain) backed by a mined lexicon (2.4k entries) and a context resolver (497 tokens, bigram tables). Corpus v2: **4,157 songs** (`CSVs Dataset/corpus_final_v2.csv` → `music_rec_artifacts/cleaned_lyrics.csv`).
3. **Recommender** (`music_rec/`): mpnet embeddings (768-d, `paraphrase-multilingual-mpnet-base-v2`, not fine-tuned) + 48-token window vectors (`window_vectors.npy`, ~62k windows, 182MB) + FAISS `IndexFlatIP`; BM25 lexical index (in-memory, `lexical.py`) with fuzzy token expansion and typo map, min-max score fusion (`lexical_weight=0.65`), exact-dup collapsing (`dedup.py`), sentiment alignment + MMR rerank (`rerank.py`), artist-name auto-filter. Query path: transliterate → encode (ONNX Runtime or torch) → hybrid → rerank.
4. **Mood**: legacy muRIL tweet-sentiment (pruned checkpoint) replaced by a **linear probe on Gemini-teacher labels** (`mood_probe.npz`, `sentiment_scores.csv`, 4,157 songs) + per-line attribution (`mood_attribution.py`, window probe aggregation, calibrated line labels) + mood vectors/neighbours (`mood_neighbors.py`).
5. **Web app** (`web_app/`): FastAPI + vendored three.js "Mood Studio" — search (title/artist + hybrid lyric), 3D donut mood explainability, per-line emotion coloring, song neighbors, mood top charts; background warmup; CPU inference.
6. **Evaluation** (`eval/`): lyric nDCG@10 0.922 / recall@10 0.950 on 4,157 songs; hard non-verbatim subset 0.932–0.957 truncated/dropped, 0.826 Romanized; artist 0.880/0.782; seed 0.156/0.024; mood retrieval precision@10 0.709 / gold hit@10 0.273; mood gold 147 songs (probe relaxed acc 0.789); line mood gold 249 lines (calibrated agreement 0.510); transliteration gold 208 lines / 743 words.
7. **Tests**: ~30 pytest files, ~130 tests. No CI config found, no container config found.

Key files: `PROJECT_GUIDE.md` (full state of the system, read it), `music_rec/README.md`, `music_rec/config.py`.

## What the user wants

A **professional-grade audit** answering: *what are the gaps between this system and real-world (Spotify / YouTube Music / Apple Music / TikTok-class) recommender systems, and what further improvements should be made?* Their stated standard: **"professional work that only lacks in scale, not scalability"** — meaning architecture should be sound enough that only data/compute/users are missing, not engineering.

Therefore classify every finding with one or more labels:

- `LACKS-SCALE` — would be fixed by more catalogue, labels, users, or compute; code is fine.
- `LACKS-SCALABILITY` — engineering/architecture would break, degrade, or underperform at 10x–1000x data/users (e.g. O(N) in-memory paths, single process, no sharding, flat ANN, no offline/online split).
- `PROD-GAP` — production hygiene missing (observability, CI/CD, config, security, error handling, model/artifact lifecycle).
- `ALGO-GAP` — algorithm/quality gap vs industry practice (personalization, learning-to-rank, query understanding, audio, feedback).
- `DATA-GAP` — training/eval data quality or coverage gap.

Be rigorous and honest. Do not pad. Every finding must cite **file:line evidence** from this repo. Compare against concrete industry practice (name systems/papers/patterns; you may use web search for current 2025–2026 state of the art). Distinguish what is genuinely good from what is POC-level.

## Required report format (write to your assigned file)

```markdown
# Track N — <name>

## 1. Scope & evidence
Files inspected, commands run, artifacts examined.

## 2. What is already strong (with evidence)
Bullet list. Be specific; praise only what is real.

## 3. Gap register
| # | Gap | Evidence (file:line) | Severity P0–P3 | Label(s) | Industry reference | Impact if 100x scale |
|---|-----|----------------------|----------------|----------|--------------------|----------------------|

## 4. Top 10 improvements (ranked by impact / effort)
For each: what to do concretely, where, rough effort (S/M/L), expected gain, dependencies.

## 5. Verdict
Does this area lack **scale** or **scalability**? One paragraph, direct.

## 6. Open questions / uncertainty
Things you could not verify, data missing, risks in your own conclusions.
```

## Rules for auditors

- **Read-only** on the repo: do **not** edit source, tests, or artifacts. The only file you may write is your own report file.
- Do **not** run full builds, training jobs, model downloads, or the whole test suite; light read-only commands (`git log`, `rg`, small `python -c` checks) are fine.
- Keep the report under ~2,500 words.
- Return a ≤400-word summary of your top findings as your final message.
