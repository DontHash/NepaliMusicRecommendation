# Project R: Nepali lyric search and music discovery

Type a fragment of a Nepali song in **Romanized Nepali** (`maya lagcha`) or **Devanagari** (`माया लाग्छ`) and get the songs it most likely comes from, plus similar songs by lyric and mood.

Nepali lyrics online are messy. They come in both scripts, with inconsistent spellings and scraping junk. This project is mostly about turning that into a clean, searchable corpus.

## What's inside

- **Corpus**: about 4,200 Nepali songs collected and cleaned from public lyric sources (4,157 at the time of the evaluation below), with deduplication, quarantine reports and no silent drops.
- **Roman → Devanagari transliteration**: a character-level Transformer (~4M parameters) with lexicon backoff. **7.47% CER** on 208 human-reviewed lyric lines (exact-line match 21%). The [report](music_rec_artifacts/transliteration_report.json) lists the worst cases too.
- **Retrieval**: hybrid BM25 + dense (multilingual sentence embeddings, FAISS) with window-level matching for verbatim lyric fragments, then MMR reranking.
- **Evaluation**: on an internal set of 40 lyric-fragment queries, **recall@10 = 0.95**, nDCG@10 = 0.92 ([eval_v2_report.json](music_rec_artifacts/eval_v2_report.json)). "More like this song" (seed) queries are much weaker (recall@10 = 0.02). That remains an open problem, and the report keeps it visible.
- **Data contracts**: every dataset has a versioned schema, and [CI](.github/workflows/data-contracts.yml) validates them on each push. The serving set is pinned by a SHA-256 artifact manifest with rollback. See [data_engineering/README.md](data_engineering/README.md).
- **Web app**: FastAPI backend with a small JS front end in [`web_app/`](web_app/).

## Run it

```bash
pip install -r requirements.txt
python scripts/run_music_rec.py audit
python scripts/run_music_rec.py embed
python scripts/run_music_rec.py index
python scripts/demo_music_rec.py --text "maya lagcha"
```

On Windows, set `$env:USE_TF = "0"` if Transformers complains about Keras. Full walkthrough: [PROJECT_GUIDE.md](PROJECT_GUIDE.md).

## Repo map

| Path | What |
|---|---|
| `data_collection/`, `lyrics_pipeline/` | Corpus harvesting and cleaning |
| `music_rec/` | Embeddings, index, retrieval, rerank |
| `eval/` | Gold sets and evaluation scripts (transliteration, retrieval, mood) |
| `data_engineering/` | Dataset schemas, validation, artifact manifest |
| `web_app/` | FastAPI server and front end |
| `audit/` | Self-audit of the system, with known gaps |

## Limitations

Lyrics only; no audio yet. Single-process serving. The evaluation sets are small and built in-house, so treat the numbers as internal benchmarks, not general accuracy.

Built by [Bhishma Bhandari](https://github.com/DontHash).
