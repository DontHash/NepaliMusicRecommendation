# scripts/audio — local audio collection pipeline

Links a local audio collection to the lyrics corpus, fetches missing lyrics, and
builds CLAP audio embeddings so audio becomes a first-class retrieval signal.

## Pipeline

| # | Script | Input | Output |
|---|--------|-------|--------|
| 1 | `build_manifest.py` | collection files + metadata (see Input contract) + `cleaned_lyrics.csv` | `audio_manifest.csv` (per file), `audio_tracks.csv` (per unique track), `manifest_report.json` |
| 2 | `fetch_lyrics.py` | `audio_tracks.csv` | `audio_lyrics.jsonl` (resumable, cached; one line per track) |
| 3 | `build_dataset_lines.py` | tracks + fetched lyrics + corpus | `audio_track_matches.csv`, `audio_file_map.csv`, `audio_new_songs_v2.csv`, `dataset_report.json` |
| 4 | `embed_audio.py` | tracks + ffmpeg (`imageio-ffmpeg`) | `audio_embeddings.npy` (CLAP 512-d, L2-normalised), `audio_embedding_keys.csv` |
| 5 | `query_audio.py` | embeddings | text→audio / audio→audio search |
| 6 | `analyze_audio_similarity.py` | embeddings | `audio_duplicate_candidates.csv`, `audio_similarity_report.json` |

```bash
python scripts/audio/build_manifest.py
python scripts/audio/fetch_lyrics.py --sample 50 --with-fallback     # validation
python scripts/audio/fetch_lyrics.py --min-artist-score 85           # targeted fetch
python scripts/audio/build_dataset_lines.py
python scripts/audio/embed_audio.py                                  # resumable
python scripts/audio/query_audio.py --text "sad acoustic guitar"
```

## Input contract (generalizable to any library)

Metadata is resolved in this order, so no script depends on this particular collection:

1. `--metadata-csv PATH` (highest precedence): columns `file` or `audio_path`,
   `artist` or `author`, `title`, `duration` or `duration_s`, optional `source`.
2. `<collection>/_index.csv` (the shipped harvest index, if present).
3. Filename parsing: `Artist - Title.ext`.

The collection root comes from `--collection` or `PROJECTR_AUDIO_COLLECTION`
(default in `config.py`). All audio is read-only.

## Artifact contract & provenance

- `config.SCHEMA_VERSION` is stamped into every report/JSONL row.
- `manifest_report.json` and `dataset_report.json` include `generated_at`,
  `git_sha`, and SHA-256 of the inputs (`_index.csv`, metadata CSV,
  `cleaned_lyrics.csv`).
- `audio_embeddings.npy` and `audio_embedding_keys.csv` are written atomically
  (tmp + `os.replace`); embedding runs are resumable and skip existing keys.
- Committed: manifests, matches, file map, new dataset lines. Ignored: fetched
  lyrics cache and embedding vectors.

## Matching logic

1. **Metadata match** (stage 1): token-set fuzzy match of normalized
   title/artist against the 4,157-song corpus; buckets
   `strong` / `probable` / `weak` / `none` (`config.py` thresholds).
2. **Lyrics confirmation** (stage 3): fetched lyrics are sanitized (LRC
   timestamps and CJK credit lines dropped), cleaned and transliterated through
   the production `LyricsCleaningPipeline`, then compared with candidate corpus
   lyrics (token-set similarity + 4-gram Jaccard).
   - ≥ `CONFIRM_SIM` (or ≥ `CONFIRM_SIM_METADATA` when metadata already points
     at the song) → link to that `song_id`.
   - ≥ `AMBIGUOUS_SIM` → linked and flagged ambiguous.
   - below → a **new dataset line** if the raw provider text is Nepali
     (`nepali_ratio` ≥ `NEPALI_MIN_RATIO`, using the transliterator's English
     gate so English songs are rejected while romanized Nepali passes),
     otherwise rejected as a foreign-language mismatch.
3. **File map**: every audio file → existing `song_id`, stable new
   `A-<sha1(track_key)[:10]>` id, or unmatched. Hash ids never shift between
   runs; final integer `song_id`s are assigned when new lines are merged.

## Lyrics providers

Tried in order, each result cached and rate-limited (`data_collection.http`,
1 req/s for `lrclib.net`):

1. LRCLIB `/api/get` with cleaned title + primary artist + duration.
2. LRCLIB `/api/search`, best pick requires title ≥ 75 and duration within 20 s.
3. `--deep`: LRCLIB query-only search.
4. `--with-fallback`: Musixmatch/NetEase via `syncedlyrics`, then sanitized and
   gated by the Devanagari share check.

Every row records `status` (`found` / `miss` / `error`) and provider for audit.

## Scale notes

- **Ingestion**: disk-cached, rate-limited, per-track resume — safe to interrupt.
- **Candidate generation**: stage 3 reuses the production sparse BM25
  (`music_rec.lexical.LexicalIndex`, fuzzy disabled), so memory scales with
  tokens, not with a char n-gram matrix.
- **Embeddings**: decode (ffmpeg, CPU) and inference (CLAP) are sequential today;
  at ~100k tracks move decode to a worker pool and shard the embeddings
  (`part-*.npy` + an index) instead of rewriting one array per checkpoint.
- **Fetch at scale**: provider chain is a plain function table; parallelise per
  host behind the existing rate limiter when provider quotas allow.

## Tests

`tests/test_audio_pipeline.py` — hermetic (no collection, no models): metadata
normalisation, provider sanitisation, verdict logic, offsets, resume helper,
artifact aliases. Gated integration checks (real corpus/collection) stay manual.

## Caveats

- LRCLIB coverage for Nepali deep cuts is partial (~10% on gap tracks);
  mainstream artists are well covered. The sites' own `/search` endpoints are
  robots-disallowed or low-yield, so they are not used.
- The collection is artist-biased and contains non-Nepali material; use it to
  build capability, not as an unbiased evaluation sample.
- Rights: downloaded audio is for internal research; do not redistribute.
