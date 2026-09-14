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
| **File (current)** | `new_char_transformer_best.pt` + `new_char_vocab.pkl` — the default |
| **File (previous)** | `char_transformer_442.pt` + `char_vocab.pkl` — kept as fallback and for `scripts/compare_transliterators.py` |
| **Trained in** | `Notebooks/NewTransliterate.ipynb` (current) / `Notebooks/FinalTransformerChar.ipynb` (first version) (Kaggle GPU) |
| **Job** | Roman letters → Devanagari characters |
| **Architecture** | Small encoder-decoder Transformer (~4M params) |
| **Training data** | Aksharantar Nepali (~300k–2.4M word pairs depending on notebook) |
| **Quality** | ~3.54% CER on validation (current); ~4.42% CER (previous) |
| **Used when** | User types `maya lagcha`; query encoding; cleaning romanized CSV rows |

**Why character-level?** Nepali transliteration is mostly spelling mapping. Words are short. A char model is small, fast, and works well.

**How it works (simple):**  
Input: `m a y a` (as character IDs) → Transformer → output: `म ा य ा` (Devanagari IDs).

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
| **Free text** | `"maya lagcha"` | Transliterate → embed → search |
| **Seed song** | `song_id=12` | Use that song’s stored vector |
| **Filtered** | text + `artist="Narayan Gopal"` | Search, then hard-filter by artist |

---

### Phase 7 — Reranking (`rerank.py`)

ANN gives top **50** by similarity. Reranking picks final **10** using:

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
| Tail truncation for sentiment | Song endings carry emotion |
| MMR reranking | Users want variety, not 10 clones |
| 932 songs not 20k | Honest POC size; architecture scales |

---

## 13. Known limitations (be aware)

1. **Small catalogue** — 932 songs. Recommendations are only as good as coverage.
2. **No real genre labels** — category is `nepali` vs `romanized`, not rock/pop/etc.
3. **Sentiment skew** — tweet-trained model + sad lyrics → mostly “negative” labels.
4. **No audio** — timbre, tempo, instrumentation ignored.
5. **No ground-truth eval** — we use proxy metrics (diversity, sentiment coherence), not human “was this a good rec?”
6. **Transliteration errors** — rare wrong characters can shift embedding slightly.

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

ProjectR turns **messy Nepali song lyrics** into a **searchable, mood-aware catalogue**. Users can type in **Roman or Devanagari**, get **similar songs**, or **analyze** a lyric’s mood and keywords. Three model families power it: a **custom transliterator**, a **fine-tuned mood classifier**, and **off-the-shelf embeddings** with **FAISS** search and **MMR** reranking.

The system is **working end-to-end** on 932 songs. Growing the dataset, fixing sentiment for song domain, and adding audio are the natural next steps.

---

*Last updated to reflect project state: 942 raw songs → 932 cleaned → full pipeline + MusicAnalyzer.*
