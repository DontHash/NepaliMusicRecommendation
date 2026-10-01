# Addendum — Local Audio Collection Assessment

**Date:** 2026-10-01
**Source:** `C:\Users\praka\Downloads\Nepali Music Collection`
**Method:** read-only inventory + filename/index-based matching against `music_rec_artifacts/cleaned_lyrics.csv` (4,157 songs) and `eval/mood_gold.csv` (147 songs). Scripts: `audit/audio_inventory.py`, `audio_match_refined.py`, `audio_index_join.py`, `audio_coverage.py`. Automation outputs: `audio_match.csv`, `audio_match_refined.csv`, `audio_index_matches.csv`, `audio_corpus_coverage.json`, `audio_index_join_summary.json`.

---

## 1. What is there

| Property | Value |
|---|---|
| Audio files | **3,663** (2,909 mp3, 729 m4a, 25 ogg) |
| Size | **29.67 GB** |
| Total duration (from index) | **~237 hours** |
| Collection tooling included | `_index.csv` (5,523 rows: sound_id, author, title, duration, source_query, file, bytes, status, url), `_duplicates.csv` (411), `_purged.csv` (1,183), scope/failure logs |
| Provenance | Mixed downloader sources (mp3.pm, SoundCloud, YouTube-like), queries mostly Nepali artists + topics |
| Top source queries | Sajjan (179), OSRDigital (168), nepali (161), Yam Baral (152), Melina Rai (142), Kunti Moktan (131), Deepak Limbu (128), Narayan Gopal (104), Sanjeev Singh (95), Nabin K Bhattarai (84) … `teej song` (74), `Nepali rap` queries, `Kutumba` (54), `Resham Firiri` (49) |

The collection is **not** a random catalogue sample: it is artist-biased (Yam Baral, Melina Rai, Kunti Moktan, Narayan Gopal, …) and contains a clearly non-Nepali minority (Bhojpuri/Banjara Teej remixes, Hindi bhajans, Pashto/Punjabi "Sajjan" songs, Western library tracks, audiobooks, instrumentals). A meaningful share is Nepali repertoire that is **not** in the lyric corpus.

## 2. How well it maps to the corpus

Filename-based conservative matching (title token-set similarity + artist corroboration, generic short titles excluded):

| Bucket (match score) | Audio files | Distinct corpus songs |
|---|---|---|
| Strong (≥92) | ~329–426 | **329** |
| Probable (≥82) | ~708 | 708 |
| Weak or better (≥70) | ~865 | 865 |
| Files whose artist is a known corpus artist (any title) | ~1,736 | — |

So roughly **8–21% of the lyric corpus has audio here**, and ~1,700 files are by corpus artists but represent other repertoire. Corpus artists best covered: Narayan Gopal (45), Bipul Chettri (17), Nepathya (12), Sushant KC (11), VTEN (11), Sabin Rai (10), Yama Buddha (9), Nabin K Bhattarai (8), Ram Krishna Dhakal (8).

**Mood-gold overlap is thin:** only **14/147 gold songs strong**, 24/147 probable, 30/147 any. Supervised audio-mood validation on human gold is therefore weak; weak supervision via the 4,157 Gemini/probe labels is viable for the matched subset.

Caveats on precision: matching is metadata-based (no listening/fingerprinting), so counts should be treated as ±10–15% until a fingerprint pass (`chromaprint`) or manual spot-check of ~30 pairs. False-positive risk concentrates in generic titles; false-negative risk in title variants (covers, "(Live)", transliteration differences).

## 3. What it is good for (ranked)

1. **Audio embeddings / second modality — the audit's biggest content gap.** Embed all 3,663 files with CLAP (text-audio joint space) and/or MERT (acoustic) on 30 s clips; 3,663 × 512 float32 ≈ 7.5 MB. Needs no corpus matching. Unlocks: audio-similarity "more like this", instrumental/timbre/melody coverage, audio-only clustering, and later text-audio queries ("sad acoustic guitar"). This is the single most valuable use.
2. **Cross-modal mood validation.** Weak-supervised audio mood head on the ~330–700 matched songs against existing mood labels; measure where text-mood and audio-mood disagree (expected: upbeat-sounding sad-lyric songs; the current probe's 82% negative skew may be a lyric-domain artifact). Directly attacks audit Track 2's biggest quality concern.
3. **Deduplication / version detection.** Chromaprint fingerprints (+ maybe cover-song detection) to cluster covers/live/remix/duplicates inside the collection and against future crawls — addresses the documented "covers and re-uploads remain separate rows" limitation (Track 3/7).
4. **Evaluation and listening tests.** Human mood/quality judgments grounded in audio; candidate-pool for "was this a good rec" listening studies the audits said are missing.
5. **Product previews — legal caveat.** Locally this is useful for development; **do not serve these files publicly**. For a product, use licensed preview URLs (iTunes `preview_url` is already collected but dropped at audit) rather than this downloader-sourced audio.
6. **Training data for an audio tower** once events exist (Phase 2/3), only if provenance/licensing is resolved.

## 4. Practical blockers to fix before a pipeline

- **Decoding:** `ffmpeg`/`ffprobe`/`fpcalc` are **not installed**; 729 `.m4a`/AAC files cannot be decoded without ffmpeg (mp3 is fine via `soundfile`). Install ffmpeg (winget/choco or `imageio-ffmpeg`) — machine-level change, ask first.
- **Audio stack:** `torchaudio` was removed from this repo due to a torch 2.6 DLL clash; use `soundfile`/`librosa` for loading and `transformers` CLAP (`laion/clap-htsat-unfused`) or MERT (`m-a-p/MERT-v1-95M`) for embeddings. GPU is an RTX 2050 (thermals) — batch 30 s clips, not full tracks.
- **Storage policy:** keep the 30 GB collection where it is; commit only a manifest and small embedding arrays; large artifacts stay gitignored.
- **Rights:** downloaded mixes; research/internal use only; keep out of Kaggle/git/public serving.
- **Bias:** artist-skewed, so do not use it as an unbiased evaluation sample; use it for capability building.

## 5. Proposed Phase A prototype (if approved)

1. `scripts/audio/build_manifest.py` — join `_index.csv` + disk, verify decodability/duration, emit `R_data/audio/audio_manifest.csv` with corpus match id + confidence (gitignored).
2. Install ffmpeg; add `soundfile`/`librosa` (+ optionally `chromaprint` via `pyacoustid`) to a separate requirements-audio file.
3. `scripts/audio/embed_audio.py` — three 10 s segments per track → CLAP embeddings (512-d) and MERT embeddings (1024-d) → `R_data/audio/audio_embeddings.npz`; log per-file failures.
4. `scripts/audio/build_audio_index.py` — FAISS HNSW/FlatIP over audio embeddings + metadata; `audio_similar(track)` debug CLI.
5. Fuse experiment: for the ~330–700 matched songs, score-level blend of text-window and audio similarity; re-run the existing retrieval eval and compare (expect paraphrase/cover gains, no regression on verbatim lyric queries).
6. Mood cross-check: linear head on CLAP/MERT vs `sentiment_scores.csv`; report agreement and the highest-disagreement examples.
7. Update the executive audit Phase 3 accordingly; keep audio out of the public product path until licensing is decided.

Exit criteria for Phase A: manifest with ≥95% decode coverage; audio index serves top-10 in <50 ms; a documented retrieval or mood result that text-only cannot produce; no redistribution of source audio.

---

## 6. Implementation status & standards (2026-10-01)

Built under `scripts/audio/` with the same discipline the audit demanded:

| Concern | Implementation |
|---|---|
| Configuration | `config.py` (schema version, thresholds, embedding model, id prefix) — no magic numbers in scripts |
| Input contract | `--metadata-csv` (portable `file/artist/title/duration` aliases) → `_index.csv` → filename parsing; collection root via `PROJECTR_AUDIO_COLLECTION` |
| Provenance | `schema_version`, `generated_at`, `git_sha`, SHA-256 of inputs in `manifest_report.json` / `dataset_report.json`; `status` field per fetched track |
| Matching | token-set metadata gate → production cleaning/transliteration → lyrics-similarity confirmation; foreign-language results rejected by the raw-text `nepali_ratio` gate (English songs rejected, romanized Nepali accepted) |
| Scale | sparse BM25 candidate generation (not char n-grams), cached/rate-limited/resumable fetch, atomic + resumable embedding saves |
| Identity | content-addressed `A-<sha1(track_key)[:10]>` provisional ids (stable across runs); integer ids assigned at corpus merge |
| Tests | `tests/test_audio_pipeline.py`, 14 hermetic tests (no collection, no models) |

Status at time of writing (run complete):

- **Manifest**: 3,650 unique tracks — 1,096 strong / 254 probable / 1,711 weak / 589 none (strict token-set matching).
- **Lyrics fetch**: 1,072 gap tracks queried (LRCLIB + Musixmatch/NetEase fallback), 90 found (8.4%);
  LRCLIB get 62 / search 17 / fallback 5 of the final 83, remainder from validation samples.
- **Dataset lines**: 3,663 audio files → **1,113 linked to 524 distinct corpus songs**, **57 new songs**
  (`A-<sha1(track_key)[:10]>` provisional ids, median 132 tokens), 2,493 unlinked (unknown lyrics or non-Nepali),
  14 foreign-language matches rejected by the `nepali_ratio` gate, 9 lyrics-confirmed + 8 ambiguous links.
- **Embeddings**: 3,650/3,650 tracks embedded with CLAP (0 decode failures, ~27 min on RTX 2050).
- **Duplicate detection**: 105 same-recording pairs at cosine ≥ 0.99 (all verified genuine on inspection).
- **Quality gates**: 15 hermetic tests + full repo suite green; CI workflow added (first in the repo).

Pending deliberate steps: merge `audio_new_songs_v2.csv` into the numbered corpus (final integer ids),
then regenerate embeddings/probe/index and re-run retrieval evals; wire audio similarity into the
recommender as a third candidate source.

**Recommender integration (A8).** `music_rec/audio_index.py` loads the CLAP artifacts;
`recommend_by_song` fuses audio similarity into the seed ranking (`Config.audio_weight=0.5`,
merging only where audio exists so text-only songs are never penalised) and
`recommend_by_audio(track_key)` ranks corpus songs by sound. The first `base_scores` branch bug
(exclusion/keep-mask applied only on the FAISS path) was found by the new tests and fixed.
Measured on 368 same-artist seed queries over the 520 audio-covered songs:
text-only nDCG@10 0.1833, audio-only 0.2436, fused@0.5 **0.2527**; paired bootstrap delta
+0.0694, 95% CI [0.0362, 0.1019], with weights 0.3/0.5/0.7 all CI-positive
(`R_data/audio/eval_audio_seed_report.json`). This is the Phase A exit criterion: a retrieval
gain text-only cannot produce, measured with uncertainty.
