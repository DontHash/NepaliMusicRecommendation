# Running the GPU-heavy steps on Kaggle

The sentiment fine-tuning and lyric embeddings are GPU-heavy. Run them on a
**Kaggle T4** notebook instead of a local CPU-only machine, then download the
artifacts into `music_rec_artifacts/` and finish the pipeline locally.

> Do **not** use Ollama for the sentiment step — it serves LLMs and cannot
> fine-tune a sequence-classification model.

## Notebooks

| Notebook | Produces | Model |
| --- | --- | --- |
| `KaggleSentimentTrain.ipynb` | `sentiment_scores.csv` + `sentiment_model/` | `google/muril-base-cased` |
| `KaggleLyricEmbeddings.ipynb` | `embeddings.npy` + `embedding_ids.json` | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` |

Both live in the project root.

## Kaggle setup (per notebook)

1. Create a new Kaggle notebook and upload the `.ipynb`.
2. **Settings → Accelerator → GPU T4 x2**.
3. **Settings → Internet → On** (needed to download models / the HF dataset).
4. **Add Input** (attach datasets):
   - Upload `music_rec_artifacts/cleaned_lyrics.csv` as a Kaggle dataset and
     attach it. If you do not have it, attach the raw
     `CSVs Dataset/Lyrics_Dataset_final.csv` instead — the notebooks auto-detect
     either schema (`lyrics` or `lyrics_devanagari`).
   - `KaggleSentimentTrain.ipynb` additionally pulls `Shushant/NepaliSentiment`
     automatically through the `datasets` library (no manual attach needed).
5. **Run All**. Outputs are written to `/kaggle/working/`.

## Download + placement

After each notebook finishes, download from `/kaggle/working/` and place into
your local `music_rec_artifacts/`:

```
music_rec_artifacts/
├── sentiment_scores.csv      # from KaggleSentimentTrain.ipynb
├── sentiment_model/          # from KaggleSentimentTrain.ipynb (optional to keep)
├── embeddings.npy            # from KaggleLyricEmbeddings.ipynb
└── embedding_ids.json        # from KaggleLyricEmbeddings.ipynb
```

These are drop-in compatible with `music_rec/sentiment.py` and
`music_rec/embeddings.py` (same columns, same float32 raw-embedding convention).

## Finish locally

Once the artifacts are in `music_rec_artifacts/`, build the rest of the
pipeline locally (CPU is fine for these steps):

```bash
python scripts/run_music_rec.py features
python scripts/run_music_rec.py index
python scripts/run_music_rec.py eval
```

## Design notes

- **Tail truncation**: lyrics longer than 256 tokens are truncated to the
  **last** 256 tokens (keep `[CLS]` + the final tokens). Song conclusions carry
  the most emotional weight, so the *end* of the lyric is kept.
- **Sentiment score**: `sentiment_score = P(positive) - P(negative)`, range
  `[-1, 1]`. Class polarity is inferred from each label's name.
- **Embeddings**: mean pooling, batch size 64, `normalize_embeddings=False`
  (raw float32). Normalization happens at index-build time, mirroring
  `music_rec/embeddings.py`.
