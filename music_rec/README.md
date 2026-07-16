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

- **Corpus is 942 (-> 932 after cleaning), not 20k.** Code scales unchanged.
- **CPU-only**: kept muRIL fine-tune but light (2 epochs); embeddings use
  `paraphrase-multilingual-mpnet-base-v2` (no fine-tune needed).
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
