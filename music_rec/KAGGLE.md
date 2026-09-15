# Running the GPU-heavy steps on Kaggle

The sentiment fine-tuning and lyric embeddings are GPU-heavy. Run them on a
**Kaggle GPU** instead of a local machine, then download the artifacts into
`music_rec_artifacts/` and finish the pipeline locally.

The lyric-embedding step is fully automated through the Kaggle CLI
(`scripts/kaggle_embeddings.py`). The sentiment step still uses the manual
notebook workflow.

> Do **not** use Ollama for the sentiment step — it serves LLMs and cannot
> fine-tune a sequence-classification model.

## Lyric embeddings (automated)

```bash
python scripts/kaggle_embeddings.py push   # create/version dataset + push kernel
python scripts/kaggle_embeddings.py wait   # poll until complete
python scripts/kaggle_embeddings.py pull   # download, validate, install artifacts
```

`push` uploads `music_rec_artifacts/cleaned_lyrics.csv` as the private dataset
`<user>/projectr-cleaned-lyrics` and pushes the GPU kernel
`<user>/projectr-lyric-embeddings-chunked` (defined in
`scripts/kaggle_jobs/lyric_embeddings.py`). `pull` downloads the outputs to
`R_data/raw/kaggle/lyric_embeddings/`, verifies that `embeddings.npy` has one
row per song and that `embedding_ids.json` matches the local `song_id` order,
then copies `embeddings.npy` + `embedding_ids.json` into
`music_rec_artifacts/`. Use `run` to do all three steps at once.

## Notebooks (sentiment)

| Notebook / job | Produces | Model |
| --- | --- | --- |
| `KaggleSentimentTrain.ipynb` | `sentiment_scores.csv` + `sentiment_model/` | `google/muril-base-cased` |
| `scripts/kaggle_jobs/lyric_embeddings.py` | `embeddings.npy` + `embedding_ids.json` | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` |

`KaggleSentimentTrain.ipynb` lives in the project root; the embeddings job is a
Kaggle script kernel pushed from `scripts/kaggle_jobs/`.

## Kaggle setup (sentiment notebook)

1. Create a new Kaggle notebook and upload the `.ipynb`.
2. **Settings → Accelerator → GPU T4 x2**.
3. **Settings → Internet → On** (needed to download models / the HF dataset).
4. **Add Input** (attach datasets):
   - Upload `music_rec_artifacts/cleaned_lyrics.csv` as a Kaggle dataset and
     attach it. If you do not have it, attach the raw
     `CSVs Dataset/Lyrics_Dataset_final.csv` instead — the notebook auto-detects
     either schema (`lyrics` or `lyrics_devanagari`).
   - `KaggleSentimentTrain.ipynb` additionally pulls `Shushant/NepaliSentiment`
     automatically through the `datasets` library (no manual attach needed).
5. **Run All**. Outputs are written to `/kaggle/working/`.

## Download + placement

`scripts/kaggle_embeddings.py pull` installs `embeddings.npy` and
`embedding_ids.json` into `music_rec_artifacts/` automatically. For the
sentiment step, download from `/kaggle/working/` and place into your local
`music_rec_artifacts/`:

```
music_rec_artifacts/
├── sentiment_scores.csv      # from KaggleSentimentTrain.ipynb
├── sentiment_model/          # from KaggleSentimentTrain.ipynb (optional to keep)
├── embeddings.npy            # auto-installed by scripts/kaggle_embeddings.py pull
└── embedding_ids.json        # auto-installed by scripts/kaggle_embeddings.py pull
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
- **Embeddings**: **chunked mean pooling** — each lyric is tokenized into
  overlapping windows (128 word pieces, stride 64), every window is encoded,
  and the window vectors are mean-pooled into one raw float32 vector per song
  (batch 256 on GPU). This covers the whole song instead of the first 128
  pieces only, which is what makes lyric-snippet queries work. Normalization
  happens at index-build time, mirroring `music_rec/embeddings.py`
  (`embed_window_tokens` / `embed_window_stride` / `embed_batch_size_gpu` in
  `music_rec/config.py`).
