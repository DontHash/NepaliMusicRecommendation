# Running the GPU-heavy steps on Kaggle

The lyric embeddings and the song-mood distillation are GPU-heavy. Run them on a
**Kaggle GPU** instead of a local machine, then download the artifacts into
`music_rec_artifacts/` and finish the pipeline locally. Both jobs are automated
through the Kaggle CLI.

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
then copies `embeddings.npy` + `embedding_ids.json` + `window_vectors.npy` +
`window_owners.npy` into `music_rec_artifacts/`. Use `run` to do all three
steps at once.

> The window artifacts are ~200MB and gitignored — regenerate with this job
> whenever a fresh clone needs window-level retrieval; the recommender falls
> back to song-level ANN if they are missing.

> Pull quirk: the Kaggle CLI skips files whose local copies look newer. After a
> rerun, delete the old files under `R_data/raw/kaggle/lyric_embeddings/` before
> `pull`, otherwise stale outputs can be "installed"; the installer's row-count
> check protects against that (it refuses mismatched files).

## Song-mood sentiment (automated)

```bash
python scripts/kaggle_sentiment.py run        # push + wait + pull (+ install)
python scripts/train_mood_probe.py            # fit probe -> sentiment_scores.csv
```

`run` pushes `<user>/projectr-sentiment-distill`
(`scripts/kaggle_jobs/sentiment_distill.py`), which:

1. labels ~2,000 songs with Qwen2.5-7B-Instruct (4-bit, internet on) using the
   five-emotion schema + 3-class sentiment. The 60 songs in `eval/mood_gold.csv`
   are excluded from the training sample deterministically (seed 42) so the
   gold set stays clean;
2. fine-tunes muRIL-base multi-label on the pseudo-labels and infers all songs.

The installer copies `sentiment_scores_v2.csv` to
`music_rec_artifacts/sentiment_scores.csv` after validating song ids.

**Status note (2026-09):** the distilled muRIL student collapsed onto label
priors (constant outputs, gold accuracy 0.42) in two runs even after switching
to fp32, warmup, and 3 epochs. The working model is instead a **linear probe on
the chunked mpnet embeddings** (`scripts/train_mood_probe.py`), which reaches
gold accuracy 0.53 vs 0.45 for the trivial always-negative baseline. The
distillation kernel stays in the repo as the documented negative result and as
the pipeline for a future relabel round (e.g. after gaining access to NepEMO /
NEmoSen, which are currently unreleased / request-only).

## Notebooks

| Notebook / job | Produces | Model |
| --- | --- | --- |
| `scripts/kaggle_jobs/lyric_embeddings.py` | `embeddings.npy` + `embedding_ids.json` + window artifacts | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` |
| `scripts/kaggle_jobs/sentiment_distill.py` | `mood_pseudo_labels.csv` + `sentiment_scores_v2.csv` | `Qwen/Qwen2.5-7B-Instruct` + `google/muril-base-cased` |
| `KaggleSentimentTrain.ipynb` | legacy tweet-trained `sentiment_model/` (MusicAnalyzer runtime) | `google/muril-base-cased` |

The two active jobs are Kaggle script kernels pushed from `scripts/kaggle_jobs/`;
the notebook is legacy (kept for the tweet-trained baseline model).

## Download + placement

Both wrappers install into `music_rec_artifacts/` automatically:
`embeddings.npy`, `embedding_ids.json`, `window_vectors.npy`,
`window_owners.npy` (embeddings job) and `sentiment_scores.csv`
(distillation job + probe). Raw outputs are kept under
`R_data/raw/kaggle/<job>/` for reference.

## Finish locally

Once the artifacts are in `music_rec_artifacts/`, build the rest of the
pipeline locally (CPU is fine for these steps):

```bash
python scripts/run_music_rec.py features
python scripts/run_music_rec.py index
python -m eval.run_eval
```

## Design notes

- **Tail truncation (sentiment)**: lyrics longer than 256 tokens are truncated
  to the **last** 256 tokens (`[CLS]` + final tokens); song endings carry the
  emotional weight.
- **Sentiment score**: `sentiment_score = P(positive) - P(negative)`, range
  `[-1, 1]`. Class polarity is inferred from each label's name. The probe
  labels use thresholds 0.0 / -0.10 (positive / negative), calibrated on
  `eval/mood_gold.csv`; probe score distribution is compressed, so a zero
  crossing is the right cut.
- **Embeddings**: **chunked mean pooling** — each lyric is tokenized into
  overlapping windows (48 word pieces, stride 24), every window is encoded, and
  the window vectors are mean-pooled into one raw float32 vector per song
  (batch 256 on GPU). The same run saves every window vector + owner map so the
  recommender can score queries by best-window similarity
  (`music_rec/window_search.py`) — 48-token windows keep a query line at ~60%
  of a window, which is what lifted lyric-query nDCG@10 from 0.10 to 0.31.
  Normalization happens at index-build time, mirroring
  `music_rec/embeddings.py` (`embed_window_tokens` / `embed_window_stride` /
  `embed_batch_size_gpu` in `music_rec/config.py`).
