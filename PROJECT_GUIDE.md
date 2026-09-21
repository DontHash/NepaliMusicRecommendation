# ProjectR — Developer Guide (Start Here)

This guide explains **what this project does**, **how the pieces fit together**, and **why each step exists**. It is written for someone who has never worked on this codebase before.

---

## 1. What is this project?

**ProjectR** is a **Nepali music intelligence system** built around song lyrics. It does three main jobs:

1. **Clean messy lyrics data** scraped from the web (Genius-style pages).
2. **Convert Romanized Nepali to Devanagari** (e.g. `maya lagcha` → `माया लाग्छ`).
3. **Recommend songs and analyze new lyrics** using machine learning (embeddings, sentiment, similarity search).

There is **no audio** in this version. Everything is based on **text (lyrics)** only. Audio is planned for later.

**Important reality check:** The original plan mentioned ~20,000 songs. The actual working dataset has **942 songs** (932 after cleaning). The code is written so it can scale to 20k+ later without major changes.

---

## 2. The big picture (one sentence)

> Raw messy CSV → clean Devanagari lyrics → train/load models → turn each song into a number vector → search similar songs when the user types Roman or Devanagari text.

---

## 3. System overview (visual)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                                     │
│  Lyrics_Dataset.csv (942 songs) → Lyrics_Dataset_final.csv               │
│  (extras archived under R_data/datasets/)                                │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              LYRICS CLEANING (lyrics_pipeline/)                           │
│  Remove: "1 Contributor", "[Chorus]", title headers, junk quotes        │
│  Transliterate: Roman → Devanagari (new_char_transformer_best.pt)       │
│  Output: Lyrics_Dataset_final.csv                                       │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              MUSIC RECOMMENDER BUILD (music_rec/)                        │
│  Phase 1: Audit & dedupe → cleaned_lyrics.csv (932 songs)              │
│  Phase 2: Sentiment (muRIL fine-tune) → sentiment_scores.csv            │
│  Phase 3: Embeddings (mpnet) → embeddings.npy                           │
│  Phase 4: Fuse features → feature_matrix.npy                            │
│  Phase 5: FAISS index → lyrics.faiss                                    │
│  Phase 6–7: Query + rerank (MMR) → top-10 recommendations               │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│  demo_music_rec.py        │   │  MusicAnalyzer.py         │
│  "Recommend songs like    │   │  "Analyze this lyric:     │
│   maya lagcha"            │   │   mood, keywords, similar"│
└───────────────────────────┘   └───────────────────────────┘
```

---

## 4. Why does this project exist?

Nepali users often type song names or moods in **Roman letters** (e.g. on phones or social media), but lyrics in the dataset are mostly in **Devanagari script**. A recommender that only understands one script would fail for many users.

So the project chains:

- A **transliterator** (custom small Transformer, ~4M parameters, ~3.5% character error on validation).
- **Multilingual NLP models** (muRIL for mood, mpnet for meaning).
- **Vector search** (FAISS) to find “songs that feel like this text.”

---

## 5. Folder structure (what lives where)

```
ProjectR/
│
├── CSVs Dataset/                    # Active lyric tables only
│   ├── Lyrics_Dataset.csv           # Original Genius scrape (942 rows)
│   └── Lyrics_Dataset_final.csv     # After cleaning + transliteration
│
├── lyrics_pipeline/                 # Cleaning + Roman→Devanagari for the CSV
├── music_rec/                       # Recommender (audit → embed → index → recommend)
├── music_rec_artifacts/             # Built model outputs (do not delete casually)
├── scripts/                         # CLI: clean, build, demo, Kaggle tooling
├── Notebooks/                       # Kaggle training notebooks
├── MusicAnalyzer.py                 # Analyze one lyric (edit LYRICS, run file)
├── new_char_transformer_best.pt     # Transliteration weights (current; ~3.5% CER)
├── new_char_vocab.pkl               # Transliteration vocabulary (current)
├── char_transformer_442.pt          # Previous weights (~4.42% CER; fallback/compare)
├── char_vocab.pkl                   # Previous vocabulary (fallback/compare)
├── requirements.txt
├── PROJECT_GUIDE.md
│
└── R_data/                          # Archived / unused (not on the hot path)
    └── datasets/                    # Word-pair corpora, extra CSVs, reports
```

---

## 6. The data story (step by step)

### Step A — Original scrape (`Lyrics_Dataset.csv`)

Each row has:

| Column   | Example |
|----------|---------|
| Category | `nepali` or `romanized` |
| Title    | Song name |
| Artist   | Singer name |
| Lyrics   | Multi-line text with **junk** mixed in |

**Typical junk inside Lyrics:**

```
1 Contributor
Euta Mancheko, Nepali Song Lyrics
[Chorus]
एउटा मान्छेको मायाले
...
```

That is **not** part of the song. It is website metadata.

### Step B — Cleaning pipeline (`lyrics_pipeline/`)

**What it removes:**

- `1 Contributor`, `2 Contributors`, …
- Lines like `Song Title Lyrics`
- `[Chorus]`, `[Verse 1]`, etc.
- `Translations` headers (on translation pages)
- Weird quotes and invisible Unicode characters
- English explanations in parentheses (on some rap songs)

**What it keeps:** Only the actual lyric lines.

**Romanized songs:** Word-by-word transliteration using `char_transformer_442.pt` so everything ends up in **Devanagari**.

**Output:** `CSVs Dataset/Lyrics_Dataset_final.csv` — 942 rows, all `lyrics_devanagari` in Devanagari script.

### Step C — Recommender audit (`music_rec/data_audit.py`)

Further cleaning for ML:

- Remove **8 exact duplicate** lyrics
- Remove **2 very short** songs (< 10 tokens)
- Normalize Unicode to **NFC** (consistent Devanagari spelling)
- Assign stable **`song_id`** (0, 1, 2, …)

**Output:** `music_rec_artifacts/cleaned_lyrics.csv` — **932 songs**.

---

## 7. The three trained models (what they are and why)

### Model 1 — Char Transformer Transliterator

| | |
|---|---|
| **File (current)** | `new_char_transformer_domain.pt` + `new_char_vocab.pkl` — domain fine-tune on teacher-labeled song lines |
| **File (previous)** | `new_char_transformer_best.pt` — Aksharantar-only baseline (fallback, and the `--checkpoint` reference for A/B runs) |
| **File (legacy)** | `char_transformer_442.pt` + `char_vocab.pkl` — first GRU-era model, kept for `scripts/compare_transliterators.py` |
| **Trained in** | `Notebooks/NewTransliterate.ipynb` (Aksharantar) then `scripts/finetune_transliterator.py` (domain fine-tune, local CPU) |
| **Job** | Roman letters → Devanagari characters |
| **Architecture** | Small encoder-decoder Transformer (~4M params) |
| **Training data** | Aksharantar Nepali (2.4M word pairs) + 24.3k denoised in-domain word pairs from 34k teacher-labeled corpus lines, 1:1 replay |
| **Quality** | Aksharantar valid 3.50% CER; test 8.45% overall (3.8% common words, 16.5%/14.2% named entities); in-domain line gold 7.47% CER / 21.1% exact, word gold 8.51% / 72.5% |
| **Used when** | User types `maya lagcha`; query encoding; cleaning romanized CSV rows |

**Decode pipeline (layered, each switchable for A/B):**

1. **English gate** — dictionary English and contraction tails stay Latin.
2. **Lexicon** (`lyrics_pipeline/translit_lexicon.py`, generated by `scripts/build_translit_lexicon.py`) — 2,408 unambiguous roman→Devanagari lookups mined from teacher labels, filtered to forms attested in natively-Devanagari songs.
3. **Context resolver** (`lyrics_pipeline/context_resolver.py` + generated `translit_context.py`) — 497 context-dependent tokens (`ma`, `ra`, `ki`, ...) pick their reading from left/right word bigrams over 93k Devanagari corpus lines, with line-boundary markers.
4. **Model** — everything else, plus fallback when the tables miss.

**Why character-level?** Nepali transliteration is mostly spelling mapping. Words are short. A char model is small, fast, and works well.

**How it works (simple):**  
Input: `m a y a` (as character IDs) → Transformer → output: `म ा य ा` (Devanagari IDs).

**Measuring it:** `scripts/check_transliteration.py` scores the committed gold sets
(`eval/translit_gold_lines.csv` 208 human lines, `eval/translit_gold_words.csv` 743 words),
the English gate, lexicon validity, and the Aksharantar test split (forgetting guard);
it writes `music_rec_artifacts/transliteration_report.json` and exits nonzero on
regression. Policy and the full metric table live in `eval/translit_policy.md`.

---

### Model 2 — muRIL Sentiment Classifier

| | |
|---|---|
| **Folder** | `music_rec_artifacts/sentiment_model/` (~906 MB) |
| **Base model** | `google/muril-base-cased` (Google’s multilingual model for Indic scripts) |
| **Fine-tuned on** | `Shushant/NepaliSentiment` (tweets, 3 classes: negative / neutral / positive) |
| **Job** | Guess the **mood** of a lyric |
| **Output per song** | `sentiment_label` + `sentiment_score` (−1 to +1) |

**Important design choice — tail truncation:**  
If a lyric is longer than 256 tokens, we **keep the end**, not the beginning.  
**Why?** In songs, the emotional punch often lands in the chorus or final lines. The beginning might be setup.

**Known limitation:** The classifier was trained on **tweets**, not songs. Nepali **lyrics** are often sad. So the model labels many songs as “negative” (737 negative vs 6 positive in our run). The **relative** score still helps reranking (similar moods cluster together).

---

### Model 3 — mpnet Embeddings (not fine-tuned)

| | |
|---|---|
| **Model name** | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` |
| **File** | `music_rec_artifacts/embeddings.npy` — shape `(932, 768)` |
| **Job** | Turn full lyric text into a **768-number vector** that captures meaning |
| **Fine-tuned?** | No — used off-the-shelf (good enough for POC) |

**Why embeddings?**  
Two lyrics with similar **meaning** should have vectors that are **close** in space. Then “find similar songs” = “find nearest vectors.”

**Mean pooling:** The model reads the whole lyric and averages internal representations into one vector per song.

---

## 8. The recommender pipeline (7 phases explained)

All phases are orchestrated by:

```bash
python scripts/run_music_rec.py <phase>
```

### Phase 1 — Audit (`data_audit.py`)

**Input:** `Lyrics_Dataset_final.csv`  
**Output:** `cleaned_lyrics.csv`, `audit_report.json`

**Why:** Bad duplicates or empty rows break search silently. This phase reports counts so you can trust the data.

---

### Phase 2 — Sentiment (`sentiment.py`)

**Input:** `cleaned_lyrics.csv` + HuggingFace NepaliSentiment  
**Output:** `sentiment_model/`, `sentiment_scores.csv`

**Why:** Mood is a useful **extra signal**. A user asking for `dukha ko geet` (sad songs) should match sad lyrics, not just similar words.

---

### Phase 3 — Embeddings (`embeddings.py`)

**Input:** `cleaned_lyrics.csv`  
**Output:** `embeddings.npy`, `embedding_ids.json`

**Why:** This is the **main content signal** for similarity. Every song becomes a point in 768-dimensional space.

---

### Phase 4 — Feature fusion (`features.py`)

**Input:** embeddings + sentiment + category + artist frequency  
**Output:** `feature_matrix.npy` — shape `(932, 772)`

**What gets concatenated:**

```
[ 768-dim embedding | 1 sentiment score | 2 category bits | 1 artist-freq bit ]
```

**Why not embedding alone?**  
Small extra dimensions let mood and metadata **nudge** results without overpowering lyric meaning. Weights are tuned so embedding still dominates.

---

### Phase 5 — FAISS index (`index.py`)

**Input:** `feature_matrix.npy` (or `embeddings.npy` if features not built)  
**Output:** `lyrics.faiss`

**How search works:**

1. Normalize all vectors to unit length (L2).
2. Use **inner product** search — for normalized vectors, this equals **cosine similarity**.
3. Given a query vector, return the **50 closest** songs quickly.

**Why FAISS?** Industry standard for vector search. 932 songs is tiny; it is instant. At 20k+ it still works well.

---

### Phase 6 — Query handler (`query.py` + `recommender.py`)

Three ways to ask for recommendations:

| Query type | Example | What happens |
|------------|---------|--------------|
| **Free text** | `"maya lagcha"` | Transliterate → dense + BM25 fusion → rerank |
| **Seed song** | `song_id=12` | Use that song’s stored vector |
| **Filtered** | text + `artist="Narayan Gopal"` | Search, then hard-filter by artist |

---

### Phase 6b — Hybrid retrieval (`lexical.py` + `dedup.py`)

Free-text search fuses two signals per song before reranking:

1. **Dense** — window max-similarity over 48-token lyric windows (falls back to
   song-level embedding cosine when window artifacts are absent).
2. **Lexical BM25** — in-memory index over the cleaned lyrics (`k1=1.5`,
   `b=0.75`) plus a bonus for songs containing the query as a contiguous token
   phrase. The query is transliterated with the same encoder as the dense path,
   so Romanized input matches Devanagari lyrics.
3. **Fusion** — both score arrays are min-max normalized and combined
   (`lexical_weight=0.65`). The lexical term is skipped when it has no signal
   (mood-only queries) and when an artist name was auto-detected.

Lexical fusion is gated by query specificity: 1-2 token keyword queries (mood
searches like `dukha` or `maya lagcha`) stay dense-only, and two-token queries
fuse only when both tokens are rare Devanagari words (a lyric fragment), never
for short English keyword pairs such as `sad song`. This protects mood search —
see the mood retrieval eval below for the measurement that motivated the gate.

Candidates are then collapsed: songs whose normalized lyrics are exactly equal
(upload duplicates) keep only the best-ranked member. Near-duplicate
heuristics (versions, covers) were tried and rejected — on this corpus they
merged distinct songs.

---

### Phase 7 — Reranking (`rerank.py`)

ANN gives top **50** candidates (fused hybrid scores for text queries, ANN for
seed songs). Reranking picks final **10** using:

1. **Cosine similarity** (primary)
2. **Sentiment alignment** with query (secondary, weight ~0.15)
3. **MMR (Maximal Marginal Relevance)** — avoids returning 10 nearly identical songs

**Why MMR?** Without it, you might get five versions of the same chorus vibe. MMR trades a little relevance for **diversity**.

---

## 9. MusicAnalyzer — analyze one lyric

**File:** `MusicAnalyzer.py` at project root.

**How to use (no command line):**

1. Open `MusicAnalyzer.py`.
2. Edit the `LYRICS = """ ... """` block near the top.
3. Run: `python MusicAnalyzer.py`

**What it returns:**

| Section | Method | Purpose |
|---------|--------|---------|
| Sentiment | muRIL | Label, score, mood name |
| Keywords | TF-IDF vs corpus | Which Devanagari words are distinctive |
| Category | k-NN on embeddings | `nepali` / `romanized` (coarse) |
| Similar songs | Nearest neighbors | Closest songs in catalogue |

**Note:** “Category” here is only script-type from the original CSV, not genre (love, rock, etc.). **Similar songs** and **mood** are the more useful outputs today.

---

## 10. Notebooks — what each one is for

Kept at `Notebooks/` (not required for day-to-day runs).

| Notebook | Run where | Purpose |
|----------|-----------|---------|
| `FinalTransformerChar.ipynb` | Kaggle GPU | First transliteration model (300k cap) |
| `NewTransliterate.ipynb` | Kaggle GPU | Better transliteration: full data, beam search, two-phase training |
| `KaggleSentimentTrain.ipynb` | Kaggle GPU | Train muRIL on NepaliSentiment + score all lyrics |
| `KaggleLyricEmbeddings.ipynb` | Kaggle GPU | Compute mpnet embeddings on GPU (faster than CPU) |

**Why Kaggle?** Fine-tuning muRIL and downloading large models is slow on a CPU-only laptop. Train on Kaggle T4, download artifacts into `music_rec_artifacts/`, finish index locally.

See `music_rec/KAGGLE.md` for step-by-step Kaggle setup.

---

## 11. How to run things (cheat sheet)

### First-time setup

```bash
pip install -r requirements.txt
```

Set environment (Windows PowerShell) if transformers complains about Keras:

```powershell
$env:USE_TF = "0"
```

### Clean raw lyrics CSV (if you have new data)

```bash
python scripts/clean_lyrics_dataset.py \
  --checkpoint new_char_transformer_best.pt \
  --vocab new_char_vocab.pkl \
  --output "CSVs Dataset/Lyrics_Dataset_final.csv"
```

### Build recommender (minimum — no sentiment retrain)

```bash
python scripts/run_music_rec.py audit
python scripts/run_music_rec.py embed
python scripts/run_music_rec.py index
```

### Full build (includes sentiment — slow on CPU)

```bash
python scripts/run_music_rec.py all --with-sentiment
```

### Try recommendations

```bash
python scripts/demo_music_rec.py --text "maya lagcha"
python scripts/demo_music_rec.py --song-id 0
```

### Analyze lyrics

Edit `LYRICS` in `MusicAnalyzer.py`, then:

```bash
python MusicAnalyzer.py
```

---

## 12. Key design decisions (and why)

| Decision | Why |
|----------|-----|
| Content-based (lyrics only) | No audio labels yet; lyrics are what we have |
| Char transliterator vs big LLM | Small, fast, 3.5% CER; fits phone/edge deployment |
| mpnet without fine-tune | Good multilingual baseline; saves training time for POC |
| FAISS instead of ChromaDB | Simpler dependencies; pandas handles metadata filters |
| BM25 fused with dense scores | Embeddings miss verbatim Nepali lines; lexical alone misses paraphrases |
| Exact-lyrics dedup only | Near-dup heuristics merged distinct versions/covers on this corpus |
| Tail truncation for sentiment | Song endings carry emotion |
| MMR reranking | Users want variety, not 10 clones |
| 932 songs not 20k | Honest POC size; architecture scales |

---

## 13. Known limitations (be aware)

1. **Small catalogue** — 932 songs. Recommendations are only as good as coverage.
2. **No real genre labels** — category is `nepali` vs `romanized`, not rock/pop/etc.
3. **Sentiment skew** — tweet-trained model + sad lyrics → mostly “negative” labels.
4. **No audio** — timbre, tempo, instrumentation ignored.
5. **Recommendation quality has no human labels** — retrieval has an objective query set, but "was this a good rec?" still uses proxy metrics (diversity, sentiment coherence).
6. **Transliteration errors** — rare wrong characters can shift embedding slightly.
7. **Duplicate uploads remain in the corpus** — only exact-duplicate lyrics are collapsed at ranking time; covers, live versions and Romanized re-uploads still occupy separate result rows.
8. **Very short lyric queries are ambiguous** — 2-4 common words (e.g. `malai maya`) cannot identify a single song; the hard eval's remaining misses are all of this kind.

---

## 14. Evaluation metrics (what the numbers mean)

From `music_rec_artifacts/eval_report.json` (example run):

| Metric | Value | Meaning |
|--------|-------|---------|
| Intra-list diversity | ~0.25 | Higher = recommended songs are more different from each other |
| Sentiment coherence | ~0.94 | Higher = recommended songs have similar mood scores |
| Catalog coverage | ~0.25 | Fraction of library that ever appears in top-10 lists (30 random queries) |

These are **sanity checks**, not proof the recommender is “correct.”

---

## 15. For new developers — suggested reading order

Read in this order to understand the flow without getting lost:

1. **`PROJECT_GUIDE.md`** (this file) — mental map.
2. **`music_rec/config.py`** — all paths and settings in one place.
3. **`lyrics_pipeline/cleaner.py`** — see what “clean lyrics” actually means.
4. **`music_rec/data_audit.py`** — how `cleaned_lyrics.csv` is produced.
5. **`music_rec/recommender.py`** — the main user-facing recommendation logic.
6. **`MusicAnalyzer.py`** — single-lyric analysis entry point.
7. **`Notebooks/NewTransliterate.ipynb`** — only if you care how transliteration was trained.

**If you want to change behavior:**

| Goal | Edit |
|------|------|
| More/fewer songs in results | `config.py` → `final_top_k`, `ann_top_k` |
| Stronger mood influence | `config.py` → `sentiment_weight` |
| More diverse results | `config.py` → lower `mmr_lambda` |
| New raw data | Re-run `clean_lyrics_dataset.py`, then `run_music_rec.py all` |
| Better transliteration | Retrain via `Notebooks/NewTransliterate.ipynb`, then replace `new_char_transformer_best.pt` + `new_char_vocab.pkl` |


---

## 16. Glossary (simple terms)

| Term | Meaning |
|------|---------|
| **Devanagari** | The script used for Nepali (e.g. माया) |
| **Romanized** | Nepali written in Latin letters (e.g. maya) |
| **CER** | Character Error Rate — lower is better for transliteration |
| **Embedding** | A list of numbers representing text meaning |
| **FAISS** | Facebook’s library for fast similarity search |
| **muRIL** | Multilingual model good for Indic languages |
| **mpnet** | A sentence embedding model |
| **MMR** | Algorithm to balance relevance vs diversity |
| **TF-IDF** | Classic method to find important words in a document |
| **POC** | Proof of Concept — works, but not production-polished |

---

## 17. Summary

ProjectR turns **messy Nepali song lyrics** into a **searchable, mood-aware catalogue**. Users can type in **Roman or Devanagari**, get **similar songs**, or **analyze** a lyric's mood and keywords. Three model families power it: a **custom transliterator**, a **fine-tuned mood classifier**, and **off-the-shelf embeddings** with **FAISS** search and **MMR** reranking.

The system is **working end-to-end** on 932 songs. Growing the dataset, fixing sentiment for song domain, and adding audio are the natural next steps.

---

## 18. Phase A corpus expansion (data_collection/)

A resumable, API-first collector now lives in `data_collection/` (SQLite WAL work
queue, cached HTTP with retries/rate limits/circuit breaker, snapshot compaction).

**Commands**

```bash
python -m data_collection.bootstrap all          # offline bootstrap corpora
python -m data_collection.enumerate              # Deezer/iTunes candidates for seed artists
python -m data_collection.crawl_sites            # lyric-site crawlers (sitemap/pagination)
python -m data_collection.harvest_lrclib         # LRCLIB per-artist harvest (best-effort)
python -m data_collection.fetch --limit 1000     # per-candidate lyrics fetch (LRCLIB)
python -m data_collection.prune                  # drop duplicate candidates
python -m data_collection.compact                # store -> R_data/corpus/corpus_raw.csv + snapshots
python -m data_collection.report --samples 5     # queue stats + random samples
```

**Result (2026-09): 932 -> 4,185 clean songs -> 4,160 after audit -> 4,157 after the C5
rebuild** (89 article page, 1855 and 1860 unrecoverable legacy rows quarantined),
sources: nepalilyrics.net (1,510), legacy 932 (735 unique), paankopat.com (561),
Kaggle Genius dump filter (373), RupeshAryal bootstrap (369), nepali-songslyrics.com
(215), nepaligeetlyrics.com (179), geetishabda.blogspot.com (151), iTunes (71),
songsdiary.com (17), Deezer (4). Duplicates/near-duplicates are removed at
compaction and audit; the cleaner strips crawler credit lines ("Lyrics:", "Cast :",
"शब्द र संगीत:", ...), site headers (Description/Romanize/Choreographer blocks),
hashtags, emojis, transliterated URLs, and title junk, which merged 21 same-song
variants at the audit step.

**Corpus hygiene rebuild (Phase C5)**

`scripts/audit_corpus_quality.py` found scrape artifacts in 903 songs (4,218 lines);
the rebuild removed all but 11 lines across 10 songs:

```bash
python scripts/audit_corpus_quality.py                    # quality report + quarantine candidates
python scripts/rebuild_corpus.py --dry-run --limit 60      # validate on a sample
python scripts/rebuild_corpus.py                           # pipeline over corpus_raw -> corpus_final_v2
python scripts/rebuild_corpus.py --assemble-only           # re-apply drop rules without re-running the model
```

- `lyrics_pipeline/transliterator.py` now has an English gate: English tokens and
  English-sentence lines pass through untouched (function-word detection), so
  English songs/code-switch stay readable instead of being phonetically
  Devanagari-ized. `lyrics_pipeline/english_lexicon.py` is generated by
  `scripts/build_english_lexicon.py` from the transliterator checkpoint.
- `lyrics_pipeline/cleaner.py` + `patterns.py` gained crawler footer/credit/site-header
  patterns in both scripts, inline artifact stripping (URLs, hashtags, emojis, embeds,
  contributor prefixes), a metadata-token detector, and a curated 140-line
  cross-song template blacklist (`lyrics_pipeline/template_blacklist.py`).
- The rebuild preserves `song_id` values (eval sets, labels, embeddings stay
  addressable); quarantine reasons live in `music_rec_artifacts/corpus_quarantine.csv`
  and dropped gold songs in `eval/gold_exclusions.csv`.
- Corpus labels v3: the 703 songs whose text changed materially (line-set Jaccard
  under 0.8) were relabeled with Gemini via `scripts/api_label.py --ids-file` and
  merged with `scripts/merge_corpus_labels.py`; 2,456 unchanged songs keep their v2
  labels. `music_rec_artifacts/mood_phrases.csv` refreshed from the merged set.

**Corpus pipeline after compaction**

```bash
python scripts/audit_corpus_quality.py                    # artifact audit + quarantine candidates
python scripts/rebuild_corpus.py                           # corpus_raw -> corpus_final_v2 + cleaned_lyrics v2
python scripts/run_music_rec.py audit --input "CSVs Dataset/corpus_final_v2.csv"
python scripts/kaggle_embeddings.py run                    # chunked embeddings + windows on Kaggle GPU
python scripts/train_mood_probe.py --pseudo R_data/raw/gemini/corpus_v3/labels_merged.csv
python scripts/run_music_rec.py features
python scripts/run_music_rec.py index
python -m eval.run_eval
python eval/queries.py --hard          # non-verbatim lyric queries (queries_hard.jsonl)
python -m eval.run_eval --queries R_data/corpus/eval/queries_hard.jsonl --report music_rec_artifacts/eval_v2_hard_report.json
python -m eval.mood_retrieval_eval     # mood/free-text retrieval vs weak + human labels
```

**Retrieval eval (2026-09 hybrid, 4,157 songs, `eval_v2_report.json`)**

| Query type | nDCG@10 | Recall@10 | MRR | Notes |
|------------|---------|-----------|-----|-------|
| artist | 0.880 | 0.782 | 0.883 | unchanged; exact artist-name detection + filter-first ranking |
| lyric | 0.922 | 0.950 | 0.913 | single-line -> source song; BM25 + dense fusion with phrase bonus |
| seed | 0.156 | 0.024 | 0.188 | unchanged seed path; noisiest metric (30 queries) |

Controls (same runner, `eval_dense_control.json` / `eval_fusion_control.json`):
dense-only `--no-lexical --no-dedup` reproduces the old lyric nDCG@10 0.258 /
recall@10 0.350; fusion-only `--no-dedup` matches the final numbers, so exact
duplicate collapsing removes duplicate result rows without moving the target.

Hard, non-verbatim lyric subset (`eval/queries.py --hard` -> 113 queries built
from the same targets; `eval_v2_hard_report.json`):

| Variant | Dense nDCG@10 | Hybrid nDCG@10 | Hybrid recall@10 |
|---------|---------------|----------------|------------------|
| truncated to 4 tokens | 0.155 | 0.957 | 0.975 |
| one middle token dropped | 0.207 | 0.923 | 1.000 |
| Romanized line | 0.148 | 0.826 | 0.879 |

The 4 remaining Roman misses are 2-4 word generic phrases (`malai maya`,
`timi maya aunu`) that cannot identify one song; dense control lives in
`eval_v2_hard_dense_control.json`.

**Mood/free-text eval (2026-09, `eval_mood_retrieval_report.json`)**

The 15 mood queries have no per-song relevance judgments, so
`eval/mood_retrieval_eval.py` scores them with two layers: weak full-corpus
Gemini labels (`R_data/raw/gemini/corpus_v3/labels_merged.csv`, precision@10)
and 147 human-reviewed songs (`eval/mood_gold.csv`, hit@10). Hybrid and
dense-only rankings are both scored:

| Ranking | precision@10 | gold hit@10 |
|---------|--------------|-------------|
| dense only | 0.709 | 0.273 |
| hybrid (gated) | 0.700 | 0.273 |

Only `desh bhakti` differs (0.80 -> 0.70 precision, gold unchanged). The first
ungated hybrid run scored 0.545 / 0.000 — the specificity gate exists because
of that measurement. Caveats: weak labels are LLM-generated and the human gold
set is small (sadness 60 / joy 50 / anger 21 songs), so treat these as
directional regression checks, not absolute quality.

History: the original baseline (artist 0.025, lyric 0.0, seed 0.277) was
measured with a broken harness (lyric source filtered out of rankings; seed
relevance polluted by empty-artist songs) and single-pass truncated
embeddings. Fixes, in order: `eval/run_eval.py` no longer removes the lyric
source; `eval/queries.py` restricts relevance to real artists;
`music_rec/recommender.py` ranks filtered queries against all matching songs;
chunked mean-pooling replaced single-pass truncation (lyric 0.0 -> 0.10); and
finally **48-token windows with max-similarity aggregation**
(`music_rec/window_search.py`, 62k windows) took lyric nDCG@10 to 0.305, since
a query line is ~60% of a 48-token window versus ~23% of a 128-token one. The
C5 rebuild re-measured 0.258 with the same query set on cleaned text (the
queries' expected lines changed script for 1,701 songs), while seed rose
0.111 -> 0.172 and artist stayed level. The hybrid pass then added the BM25
index (`music_rec/lexical.py`), contiguous-phrase bonus, score fusion and
exact-upload dedup (`music_rec/dedup.py`), plus two tokenizer fixes (indic
tokenization glued newlines onto line-final tokens; the transliterator emits
legacy two-part vowels `ा+े` now composed to `ो`), taking lyric nDCG@10
0.258 -> 0.922 and recall@10 0.350 -> 0.950; artist and seed paths bypass the
lexical term and are unchanged.

**Song-mood sentiment (Phase C3)**

`eval/mood_gold.csv` holds 147 hand-reviewed songs (3054, 1855, 1860 excluded —
see `eval/gold_exclusions.csv`). Sentiment is
stored as two binaries (`positive`, `negative`; both = mixed, neither = neutral)
plus an explicit `polarity` column; the five emotions are multi-label, with
`primary_emotion` marking the dominant one (`none` when no core emotion
applies). Metrics (`mood_gold_report.json`, `mood_teacher_report.json`):
per-class binary F1 plus a relaxed accuracy where mixed gold songs accept a
positive OR negative prediction.

| Model | Relaxed acc | F1(pos) | F1(neg) |
|-------|-------------|---------|---------|
| Always-negative baseline | 0.564 | 0.000 | 0.721 |
| Original muRIL, tweet-trained | 0.456 | 0.000 | 0.724 |
| Linear probe on Qwen labels (previous) | 0.557 | 0.207 | 0.755 |
| Qwen2.5-7B teacher, production prompt (v1 60 only) | 0.596 | 0.400 | 0.716 |
| Gemini 3.5-flash, v2 prompt (gate, 90 songs) | 0.911 | 0.811 | 0.851 |
| **Linear probe on Gemini labels v3 (installed)** | **0.789** | **0.734** | **0.734** |

Annotation policy (from the 2026-09 semantic audit): label the emotion the song
expresses, not its topic (romance is not automatically joy; breakup is not
automatically sadness); `depression` requires sustained hopelessness, not mere
sadness; for mixed sadness/anger songs pick the primary by stance — pain/loss
maps to sadness, accusation/confrontation to anger.

The corpus relabel (2026-09) was run with free-tier Gemini keys through
`scripts/api_label.py` + `scripts/run_corpus_labeling.ps1`: all 4,011
non-gold songs labeled in ~30-song batches with schema-constrained JSON
(positive/negative binaries, five emotions, a Nepali `mood_phrase`), eight gold
few-shot examples excluded from metrics, sharded across keys and rotating over
flash models on quota resets. The C5 rebuild relabeled the 703 songs whose text
changed materially into `R_data/raw/gemini/corpus_v3/labels_merged.csv` (label
set v3). The installed probe (`music_rec_artifacts/sentiment_scores.csv`) is
retrained on those labels; emotion F1 on gold: joy 0.65, sadness 0.69, anger
0.37, fear 0.00, depression 0.00 (fear and depression are out of scope for now —
too sparse to learn; joy still over-flags romance/devotion). Mood phrases
are stored in `music_rec_artifacts/mood_phrases.csv` for a future semantic
mood-search feature. `MusicAnalyzer.py` now runs this probe at runtime (same
chunked-encoder recipe; verified by `scripts/check_probe_parity.py` — 25/25
label agreement, cosine 1.0 vs stored embeddings) and reports the in-scope
emotions joy/sadness/anger; the muRIL path (`music_rec/sentiment.py` +
`sentiment_model_dir`) is legacy and kept for reference only.

The previous probe was trained on Qwen2.5-7B-Instruct (4-bit, Kaggle)
pseudo-labels (~1,900 songs); it was replaced because the Qwen teacher
over-labeled negatives (87%) and left anger/fear nearly unlearnable. The muRIL
student collapsed onto label priors twice (constant outputs; see
`mood_gold_report_muril_v2.json`) — documented negative result. NepEMO and
NEmoSen (public Nepali emotion corpora) are unreleased / request-only.

**Line-level mood gold (v3)**

`eval/line_mood_gold.csv` labels distinct non-empty lyric lines (249 lines across
16 songs; joy 46 / sadness 57 / anger 44 / neutral 102) with per-line
emotion/polarity, a cue taxonomy, difficulty, and a one-line justification; the
rubric is written in `eval/line_mood_policy.md`. v2 applied the rebuilt corpus
(artifact lines excluded rather than labeled, quarantined songs 1855/1860
dropped); v3 folds the gold-standard review
(`eval/line_mood_review_gold_standard_check.md`) — six corrections accepted
(263:15, 757:2, 1469:0, 1469:13, 1511:19, 3174:14), policy rules 1 and 4
amended, `source` bumped to `user_v2`. `scripts/build_line_mood_gold.py` rebuilds
the CSV from the hand-authored `LABELS` dict positionally against
`cleaned_lyrics.csv` (so script-only edits such as हे -> Hey keep their labels)
and validates line counts per song; `tests/test_line_mood_gold.py` checks
vocabulary, text drift, occurrence counts, and coverage.
`scripts/build_line_review.py` writes the human review kit
(`eval/line_mood_review.csv` + `.md`) with the probe's current per-line pick next
to each label and empty `user_emotion`/`user_note` columns.

`scripts/check_line_attribution.py` sweeps aggregation modes (overlap mean,
squared-overlap, per-window hard votes, elementwise max) against neutral floors
and runs leave-one-song-out per-emotion bias calibration; the report is
`music_rec_artifacts/line_attribution_tuning.json`. The sweep picked overlap-mean
at floor 0.55 (macro-F1 0.410 vs 0.345 at the old 0.45) and a stable bias vector
`(-0.08, -0.12, +0.12)` (15/16 folds), both adopted in
`music_rec/mood_attribution.py` as `LINE_FLOOR` / `LINE_BIAS`. Calibrated line
labels agree with the gold on 127/249 lines (0.510) versus 89/249 (0.357)
before; the probabilities shown in the UI stay uncalibrated.

**Mood Studio web app (Phase C4)**

`scripts/run_web_app.py` launches a local 3D explainability UI (FastAPI +
vendored three.js, no build step) at http://127.0.0.1:8000:

- `music_rec/mood_attribution.py` probes every cached 48-token window vector
  of a song (or freshly encoded windows for pasted text), maps windows back to
  lyric lines via fast-tokenizer character offsets, and aggregates per-line
  joy/sadness/anger probabilities plus a normalized three-emotion composition.
- The frontend renders an animated 3D donut (joy green, sadness blue, anger
  red) with orbit/zoom, hover-lift tooltips, click-to-filter that dims other
  segments, a polarity gauge, the Nepali mood phrase, and lyric lines in **soft
  mode** by default: text color encodes each line's soft emotion and signal
  strength (pale / mid / saturated ramps per emotion, neutral below 0.18),
  and a `soft | hard` toggle in the panel head restores the calibrated floor
  labels. Selecting a donut segment or legend chip fades lines continuously by
  emotion affinity; hovering a line lights up its arc.
- Validation (`scripts/check_attribution.py`): 0/8 window-count mismatches
  against the Kaggle-built cache, composition argmax matches gold primary for
  6/8 sampled songs (misses: an anger song read as joy at window level, and
  the deliberately mixed joy/sadness song Asaar), and text-mode attribution is
  identical to corpus mode (max share delta 0.0000). Window-level probing is
  an approximation of the song-level probe; the gold validation bounds it.
- Mood-aware browsing: `scripts/build_mood_vectors.py` derives per-song
  joy/sadness/anger vectors (`music_rec_artifacts/mood_vectors.csv`) from the
  probe scores, and `music_rec/mood_neighbors.py` serves nearest-mood
  neighbours (`GET /api/song/{id}/neighbors?k=`, Euclidean in joy/sadness/anger
  space) plus per-emotion top lists (`GET /api/mood/top?emotion=&k=`) over all
  4,157 songs. The Studio shows a
  glass neighbours card with joy/sadness/anger chips — clicking a row loads
  that song, chips switch the card to the emotion's top chart.
- API: `GET /api/search`, `GET /api/song/{id}`, `GET /api/song/{id}/neighbors`,
  `GET /api/mood/top`, `POST /api/analyze` (`web_app/server.py`); tests in
  `tests/test_web_app.py` skip when the gitignored window artifacts are absent.

**Known limits at this stage**

- LRCLIB's artist-only search is unreliable (503/empty); per-candidate
  track+artist search is the working path (resumable via `fetch --retry-missed`).
  ~26.9k enumerated iTunes/Deezer candidates remain unfetched (deferred; low
  LRCLIB yield for Nepali).
- songsdiary.com listings are JS-driven with a robots-disallowed data endpoint:
  needs the Scrapling browser tier (planned, not enabled).
- The Kaggle Genius dump only contains ~1,530 Nepali-labelled rows.
- Sentiment is negative-skewed (probe: 82% negative) and anger/fear labels are
  too sparse to learn (teacher labeled 44 anger songs in 1,934). Non-Nepali
  (Hindi) content also slips into the corpus via artist catalogues.
- Window artifacts (`window_vectors.npy`, ~200MB) are gitignored; regenerate via
  `scripts/kaggle_embeddings.py run`. Embedding is Kaggle-first (local GPU
  avoided for thermals); `music_rec/embeddings.py` keeps a CPU chunked fallback.
- Residual corpus noise after C5: 11 artifact-ish lines across 10 songs (chord
  charts written as `सी#एम`, stray "video" prose) and some English blog prose that
  the cleaner's metadata rules do not classify; the English gate keeps such prose
  in Latin script instead of mangling it. `R_data/raw/gemini/corpus_v2` labels are
  superseded for 703 songs by `corpus_v3/labels_merged.csv`.
- `sentiment_scores.csv` now holds the mood probe's outputs (not the legacy Kaggle
  muRIL distill); `MusicAnalyzer` and the recommender read it directly, which is
  what keeps parity at 25/25.

---

*Last updated to reflect project state: C5 corpus hygiene rebuild (4,157 songs,
11 artifact lines, English-preserving gate) + labels v3 + rebuilt embeddings,
probe, index, and line-gold v2.*
