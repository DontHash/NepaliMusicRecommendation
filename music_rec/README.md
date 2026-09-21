# Nepali Lyrics Music Recommender (content-based POC)

A working content-based music recommendation system over Nepali song lyrics.
Romanized Nepali queries are transliterated to Devanagari (using the
`char_transformer_442.pt` model), embedded, and matched against song vectors.

## Status

POC complete and working on **932 songs** (cleaned from `Lyrics_Dataset_final.csv`).
Runs fully on **CPU**. Designed to scale to 20k+ songs without code changes.

## Pipeline

| Phase | Module | Output |
|------|--------|--------|
| 1. Audit & normalize | `data_audit.py` | `cleaned_lyrics.csv`, `audit_report.json` |
| 2. Sentiment (muRIL) | `sentiment.py` | `sentiment_scores.csv`, `sentiment_model/` |
| 3. Lyric embeddings | `embeddings.py` | `embeddings.npy` (mpnet, 768-d) |
| 4. Feature fusion | `features.py` | `feature_matrix.npy` (772-d) |
| 5. FAISS index | `index.py` | `lyrics.faiss` (IndexFlatIP, cosine) |
| 6. Query handler | `query.py` | seed / free-text / filtered |
| 6b. Hybrid retrieval | `lexical.py` | BM25 lexical scores fused with dense scores |
| 6c. Duplicate collapsing | `dedup.py` | exact-upload duplicates removed from results |
| 7. Rerank (MMR) | `rerank.py` | top-10 diversified |
| Eval | `evaluate.py` | `eval_report.json` |

All artifacts land in `music_rec_artifacts/`.

## Build

```bash
pip install -r ../requirements.txt

# Core content-based recommender (fast):
python ../scripts/run_music_rec.py audit
python ../scripts/run_music_rec.py embed
python ../scripts/run_music_rec.py index

# Optional sentiment dimension (slow on CPU, ~50 min muRIL fine-tune):
python ../scripts/run_music_rec.py sentiment

# Fuse + rebuild + evaluate:
python ../scripts/run_music_rec.py features
python ../scripts/run_music_rec.py index
python ../scripts/run_music_rec.py eval

# Or everything at once:
python ../scripts/run_music_rec.py all --with-sentiment
```

## Query

```bash
# Romanized free-text (auto-transliterated):
python ../scripts/demo_music_rec.py --text "maya lagcha"
python ../scripts/demo_music_rec.py --text "dukha ko geet"

# Seed song:
python ../scripts/demo_music_rec.py --song-id 0

# Filtered:
python ../scripts/demo_music_rec.py --text "maya" --artist "Narayan Gopal"
```

```python
from music_rec.recommender import MusicRecommender
rec = MusicRecommender.load()
rec.recommend_by_text("maya lagcha")          # Romanized -> Devanagari -> embed
rec.recommend_by_song(0)                       # seed song
rec.recommend_by_text("dukha", category="nepali")
```

## Design notes / deviations from the original plan

- **Hybrid retrieval (2026-09)**: free-text search fuses a BM25 lexical index
  over the lyrics (plus a contiguous-phrase bonus) with the dense
  window/embedding scores (`lexical_weight=0.65`), then collapses
  exact-duplicate uploads. Fusion is gated by query specificity: 1-2 token mood
  keywords stay dense-only; two-token queries fuse only when both tokens are
  rare Devanagari words (lyric fragments). Lyric-line retrieval went from
  nDCG@10 0.258 / recall@10 0.350 (dense only) to 0.922 / 0.950; the hard
  non-verbatim subset (`eval/queries.py --hard`) scores 0.923-0.957 for
  truncated/dropped lines and 0.826 for Romanized lines. Mood/free-text
  retrieval is measured separately (`eval/mood_retrieval_eval.py`) and matches
  the dense-only baseline. Near-duplicate collapsing was tried and rejected:
  on this corpus it merged distinct versions and covers.
- **Corpus is 942 (-> 932 after cleaning), not 20k.** Code scales unchanged.
- **CPU-only**: kept muRIL fine-tune but light (2 epochs); embeddings use
  `paraphrase-multilingual-mpnet-base-v2` (no fine-tune needed).
- **Web app runs embedding inference on CPU** (`PROJECTR_EMBED_DEVICE=cpu`,
  set by `scripts/run_web_app.py`): sharing the GPU with the browser's WebGL
  renderer caused context loss and an intermittent `/api/analyze` 500. Override
  the env var to use CUDA.
- **ChromaDB skipped**: FAISS + pandas metadata filter is simpler for this scale.
- **Sentiment truncation**: long lyrics truncated to the LAST 256 tokens
  (conclusions carry emotional weight), per the plan.
- **Sentiment skews negative** (737 neg / 189 neutral / 6 pos): muRIL was tuned
  on tweets, and Nepali lyrics skew melancholic — a domain-shift effect. The
  signal is still useful for *relative* reranking (sentiment coherence ~0.94).
  To improve later: fine-tune sentiment on song-domain data or calibrate scores.

## Future work (out of POC scope)

- Audio features (deferred per request).
- Song-domain sentiment fine-tuning / score calibration.
- Year/genre metadata (not present in current CSV).
- muRIL-based embeddings (fine-tuned) instead of mpnet.
