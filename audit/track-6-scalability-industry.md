# Track 6 — End-to-end scalability and industry-reference architecture

## 1. Scope & evidence

Inspected (read-only): all of `music_rec/`, `web_app/server.py`, `scripts/run_music_rec.py`, `scripts/kaggle_embeddings.py` + its job, `data_collection/{state,http,compact}.py`, `lyrics_pipeline/transliterator.py`, `MusicAnalyzer.py`, `PROJECT_GUIDE.md` §3–8/§18, `music_rec/README.md`, tests/CI config, artifacts. Timings against committed artifacts:

| Measurement (4,157 songs / 62,055 windows / d=768) | Result |
|---|---|
| `cleaned_lyrics.csv` pandas load | 0.08 s (10.1 MB) |
| BM25 build (`LexicalIndex`, incl. fuzzy ngram map) | **3.16 s**, vocab 60,597, nnz 330,510 |
| BM25 query `तिम्रो माया` | **92 ms** (phrase scan dominates) |
| Window matvec `(62055,768)@q` | **55 ms** |
| `np.maximum.at` owner aggregation | 1 ms |
| FAISS `IndexFlatIP` search k=50 | 0.8 ms (d=772, ntotal 4157) |
| Artifacts on disk | window_vectors 181.8 MB; embeddings/feature/index 12.2 MB each; ONNX encoder 1.07 GB |

Data flow (Q1). **Offline (manual, one machine + Kaggle):** collector → `corpus_raw.csv` (`data_collection/compact.py:22-36`) → `rebuild_corpus.py` → `data_audit` assigns `song_id = row position` (`music_rec/data_audit.py:68-69`) → whole `cleaned_lyrics.csv` pushed as a Kaggle dataset, encoded by one GPU kernel, pulled and order-validated (`scripts/kaggle_embeddings.py:83-112,171-212`) → `embeddings.npy` + `window_vectors.npy` → mood probe → static feature concat (`music_rec/features.py:19-49`) → `IndexFlatIP` (`music_rec/index.py:11-17`). **Online (one process):** single uvicorn worker (`run_web_app.py:36`) → sync routes → title/artist `str.contains` scan (`web_app/server.py:126-132`) → transliterate+encode (`music_rec/query.py:43-55`) → window matvec (`music_rec/window_search.py:39-42`) → BM25 fusion (`lexical.py:233-277`) → dedup → MMR (`rerank.py:26-46`).

Single-process/in-memory/O(N)/batch-only: **every component.** `MusicRecommender.__init__` loads CSV, embeddings, feature matrix, FAISS into RAM (`recommender.py:40-55`); BM25 + fuzzy ngram map is lazily built in-process (`lexical.py:73-101,145-153`); `WindowIndex` loads the full 182 MB npy (`window_search.py:29-32`) and `MoodAttributor` a *second* copy (`mood_attribution.py:190-195`). Corpus-wide loops run in the query path (`recommender.py:129-135,160,227-228,264`, `lexical.py:234,264-277`, `mood_attribution.py:284`, `mood_neighbors.py:78-81`). IDs are positional; artifacts are valid only as a set (`data_audit.py:69`; `kaggle_embeddings.py:187-191`).

## 2. What is already strong (with evidence)

- **Real two-stage retrieval**: 50 ANN candidates → heuristic rerank to 10 (`config.py:56-57`, `rerank.py:15-46`) — the industry funnel, not yet learned.
- **Hybrid lexical+dense with evidence-gated fusion**: BM25 + phrase bonus + fuzzy typo expansion; fusion disabled for mood keywords because the ungated run regressed to precision 0.545 (`PROJECT_GUIDE.md:649-666`; `lexical.py:191-216`). Lyric nDCG@10 0.922 / recall 0.950 with controls (`PROJECT_GUIDE.md:623-647`).
- **Conscious artifact-contract hygiene**: Kaggle pull validates row-count and id-order and rejects non-finite vectors (`kaggle_embeddings.py:185-203`); corpus rebuild preserves `song_id` so labels/embeddings stay addressable (`PROJECT_GUIDE.md:597-599`).
- **Serving-path pragmatism**: shared model singleton (`embeddings.py:58-75`), ONNX encoder with parity gate (2.4 s load, 0.02 s/query vs ~14 s/0.2 s torch; `README.md:103-108`), warm-aware lexical search while dense loads (`server.py:189-199`).
- **Resumable collector**: SQLite WAL queue, per-host rate limits, disk cache, circuit breaker (`state.py:76-83`, `http.py:55-65,114-166`).
- **Explainability + eval discipline**: per-line mood via window→line offsets (`mood_attribution.py:207-226`), calibrated (`PROJECT_GUIDE.md:761-769`); ~25 pytest files and parity scripts with nonzero exits.

These are scale-limited, not POC-nonsense; the gaps are the data plane and the missing loop.
## 3. Gap register

Severity: P0 = blocks 100×; P1 = breaks at 100×; P2 = breaks at 1000×; P3 = hygiene. Labels per brief.

| # | Gap | Evidence (file:line) | Sev | Label(s) | Industry reference | Impact if 100× |
|---|-----|----------------------|-----|----------|--------------------|----------------|
| G1 | Every request-scoped artifact is loaded whole into one Python process; no service split, no bounded memory | `recommender.py:40-55`; `server.py:88-93`; `mood_attribution.py:190-195` | P0 | LACKS-SCALABILITY, PROD-GAP | Spotify: separate retrieval/ranking services over an embedding index (MLOps.community interview) | 415k songs → ~19 GB window vectors (loaded twice) + GBs of DataFrames → OOM |
| G2 | Window search is an exact O(W) matvec; attributor scans all owners and recomputes line spans per song | `window_search.py:39-42`; `mood_attribution.py:207-226,284` | P0 | LACKS-SCALABILITY | Window/sub-item ANN or precomputed per-song aggregates; precomputed span/offset tables | 100k: ~1.3 s/query; 1M: ~13 s and 46 GB |
| G3 | BM25 rebuilt at process start (tokenize, vectorize, full fuzzy ngram map) | `lexical.py:73-101,145-153`; 3.16 s measured | P1 | LACKS-SCALABILITY | Serialized inverted index (Lucene/OpenSearch) built by a batch job | 100× → ~5 min blocking warmup per replica; 1M → ~13 min |
| G4 | `IndexFlatIP` exact search, single unsharded file, rebuilt offline only | `index.py:11-17` | P1 | LACKS-SCALABILITY | HNSW/IVF-PQ/ScaNN/Voyager ANN + sharding | 1M: ~190 ms/query/core and 3 GB index; no QPS headroom |
| G5 | Corpus-wide O(N) pandas scans on the hot path (title/artist contains, per-query `casefold`, filter mask, `embeddings @ q`, row-index dicts) | `server.py:126-132`; `recommender.py:129-135,160,227-228,264`; `recommender.py:43` | P0 | LACKS-SCALABILITY | Dedicated search service; cached normalized indices | First keystroke costs full-corpus string ops; 1M rows ≈ 0.5–2 s and ~1 GB dicts |
| G6 | Build pipeline is manual, Kaggle-bound, full-rebuild-only; no scheduler, registry, or lineage | `run_music_rec.py:65-81`; `kaggle_embeddings.py:83-112,239-246` | P0 | LACKS-SCALABILITY, PROD-GAP | Airflow/Dagster + MLflow + Ray batch; incremental re-embedding | 415k → ~6.2M windows ≈ 19 GB, past Kaggle 9 h/20 GB envelope; rebuilds take days |
| G7 | Positional `song_id`; no canonical content ID (ISRC/MBID) in the recommender corpus; append/delete invalidates all artifacts | `data_audit.py:68-69`; `kaggle_embeddings.py:187-191`; ISRC exists only upstream `data_collection/state.py:21-22` and is dropped | P1 | LACKS-SCALABILITY, DATA-GAP | ISRC/MBID canonical IDs, versioned index + alias swap (Elasticsearch-style), content hash per artifact | Any catalogue insert/merge forces global re-embed + probe + eval rebuild |
| G8 | No user model, events, or feedback; search is anonymous content retrieval | `server.py` logs only exceptions (`server.py:30,68`); no events table | P0 | ALGO-GAP, LACKS-SCALABILITY | Streaming events → real-time features → two-tower + LTR (TikTok: 10M+ events/s, 60 s feedback) | 100× data without a loop still cannot personalize; training data never accumulates |
| G9 | No offline/online feature split or feature store; features baked into `feature_matrix.npy` at build | `features.py:19-49`; `feature_meta.json` only | P1 | LACKS-SCALABILITY, PROD-GAP | Feast (offline Parquet + online Redis) at inference | Any feature change = full rebuild; ranking cannot use recency/session/popularity |
| G10 | No learned ranker; fusion/MMR weights are hand-tuned constants | `config.py:56-70`; `rerank.py:15-46` | P1 | ALGO-GAP | LightGBM/DNN LTR on impression logs (YouTube MMoE) | Quality plateaus; no objective to optimize with more data |
| G11 | No popularity/freshness/release metadata; `category` + artist frequency are the only item features | `features.py:38-46`; `music_rec/README.md:121`; `bootstrap.py:24` has `year/views` but they never reach the corpus | P1 | DATA-GAP, ALGO-GAP | Popularity/freshness/age are standard ranking inputs | Long-tail items get no prior; new releases invisible |
| G12 | No audio modality anywhere; lyrics-only | no audio deps in `requirements.txt`; `cleaned_lyrics.csv` drops `preview_url` at audit (`data_audit.py:71-80` vs `compact.py:34`) | P1 | ALGO-GAP, DATA-GAP | CLAP/MERT/Music2Vec audio embeddings fused with text; audio-text shared space | Cannot represent instrumentals, timbre, melody, covers, or perceived mood |
| G13 | Unbounded in-memory payload cache; no response/query cache, no rate limit | `server.py:72,218`; per-query re-encode `query.py:52-54` | P2 | LACKS-SCALABILITY, PROD-GAP | Redis LRU + edge/CDN; cached query→embedding | Unbounded growth; repeated query cost under QPS |
| G14 | Single uvicorn worker; CPU in-process inference; no Triton/ONNX server, replicas, or LB | `run_web_app.py:36`; `server.py:112-114`; `server.py:22` | P1 | LACKS-SCALABILITY, PROD-GAP | Triton/ONNX server; N stateless API replicas | One core encodes ~20 ms/query (`README.md:105`); ~2–5 concurrent users saturate |
| G15 | Collector is single-process SQLite; loads the entire dedupe-key set and appends to a JSONL cache index under one lock | `state.py:76-83,283-284`; `http.py:203-208` | P2 | LACKS-SCALABILITY | Distributed queue/DB (Postgres, Kafka) and partitioned fetchers | 1M candidates → GB-scale key sets per enumerate; single-writer ceiling |
| G16 | Rights/licensing metadata absent | corpus columns are `song_id,title,artist,category,lyrics,token_count` (`data_audit.py:71-80`); crawler sources tracked only in SQLite | P2 | PROD-GAP, DATA-GAP | Delivery rights/territory/ownership gate what may be recommended | Cannot ship commercially; cannot filter by licensed territory |
| G17 | No CI, container, or deployment config; observability is stdout/tracebacks only | no Dockerfile/CI found (`glob` empty); `run_web_app.py:36`; `server.py:66-69` | P2 | PROD-GAP | Containerized CI/CD, canary, Prometheus/OTel | Cannot operate or A/B anything even today |
| G18 | MMR is O(K²) Python but K is fixed at ~50 candidates | `rerank.py:26-46` | — | ALREADY SCALABLE (bound by candidate count) | Standard re-rank stage | None up to any N; only quality would change |

Component breakpoints (measured current constants extrapolated linearly; windows ≈ 14.9/song, window bytes ≈ 45.9 KB/song, BM25 nnz ≈ 79.5/song):

| Component | 10k songs | 100k | 1M | 10M | QPS ceiling today |
|---|---|---|---|---|---|
| CSV + pandas corpus | 0.2 s | ~2 s / 240 MB | ~20 s / 2.4 GB (object RAM 4–8 GB) | ~200 s / 24 GB+ (does not fit) | per-process reload |
| embeddings.npy (d=768 f32) | 31 MB | 307 MB | 3.1 GB | 31 GB | memory-bound |
| window vectors + matvec | 459 MB / 0.13 s | 4.6 GB / **1.3 s** | 46 GB / **13 s** | 458 GB / 2.2 min | **<1 QPS at 100k** |
| FAISS FlatIP search | 2 ms | ~19 ms | ~190 ms | ~1.9 s | ~single-digit QPS/core |
| BM25 build/query | 7.6 s | **~76 s / ~0.1 s** | ~13 min | ~2 h+ | every replica start |
| MMR/candidates (K=50) | unchanged | unchanged | unchanged | unchanged | scalable as-is |
| mood attributor / song | 0.4 MB/song load | 4.6 GB load | 46 GB | 458 GB | P0 break earlier |
| Kaggle rebuild | minutes | near limits (4.6 GB output) | **exceeds 9 h/20 GB** | impossible | — |

Q4 — industry essentials missing: offline/online feature split; feature store; event pipeline/user signals (no query logs); canonical content IDs; a learned ranker (two-stage retrieval **is** present); real-time signals; experimentation; audio; rights metadata; popularity/freshness; user cold-start (item cold-start is covered by content vectors); service contracts; multi-tenant paths. Gaps G7–G12, G16–G17 map to these.

## 4. Top 10 improvements (ranked by impact / effort)

1. **Split build plane from serving plane with a DAG + registry** (M–L). Airflow/Dagster around the phase scripts, MLflow for artifacts, MinIO/S3 for blobs, Ray/rented-GPU batch instead of Kaggle push/pull. Unblocks incremental re-embedding, rollback, and everything below.
2. **ANN index + serialized lexical index** (S–M). Replace `IndexFlatIP` with FAISS HNSW/IVF-PQ (or Voyager/ScaNN); persist BM25 postings/ngram map. Removes multi-minute startup and gives QPS headroom to 1M songs.
3. **Fix the window path** (M). ANN over windows (top windows → songs) instead of a 46 GB matvec; `MoodAttributor` reads per-song slices from a memory-mapped store. Preserves max-sim quality (`PROJECT_GUIDE.md:668-686`) without the P0 cliff.
4. **Remove every O(N) hot-path scan** (S). Cache normalized artist/title columns or serve from OpenSearch/SQLite FTS; compact row maps; cache query→embedding. A day's work, 1000× latency win at scale.
5. **Canonical IDs + versioned manifests** (S–M). ISRC/MBID where available, `song_id` surrogate plus `content_hash`; corpus/embedding/index versions; append-only updates with alias swaps (G7).
6. **Start the feedback loop: log every request/candidate/click** (M). Postgres or S3 Parquet for queries, ranked candidates, scores, clicks/skips; Redpanda/Kafka later. Highest-leverage ALGO investment; prerequisite for G8/G10.
7. **Online feature plane: Feast + Redis** (M–L). Sentiment, mood, popularity, freshness, then user/session features out of numpy files; served per request.
8. **Two-tower + learned ranker once events exist** (L). Item tower over content (text/mood/artist/year, audio later); user tower over history; ANN retrieve 500 → LightGBM/DNN LTR (Triton/ONNX) → policy rerank (keep MMR for diversity).
9. **Audio path on preview URLs already collected** (M–L). Carry `preview_url` into the catalogue (`state.py:21`, `compact.py:34`, dropped at `data_audit.py:71-80`), batch MERT/CLAP on previews, fuse, index alongside. See §6.
10. **Serving hardening: Triton/ONNX + replicas + bounded caches** (M). Containerize; N stateless workers behind nginx; Redis LRU for payloads and query embeddings; Prometheus + CI.

### Target reference architecture — 100k songs / 1M users (Q5)

```
OFFLINE (Airflow/Dagster on one GPU box + CPU workers)
 sources → Postgres catalogue (ISRC/MBID, rights, year, popularity) ──┐
 audio previews → MinIO/S3 → Ray batch MERT/CLAP → audio_emb.parquet │
 lyrics → existing cleaner/transliterator (containerized) → text emb ─┤
 labels/events → S3 Parquet (lake) ──────────────┐                    │
                                                  ▼                    ▼
                                   MLflow: model + index versions   Feast offline store
                                   (item emb, user tower, LTR)          │
                                   FAISS HNSW/IVF-PQ index → MinIO      │
ONLINE (k8s/compose, multi-replica)                                     ▼
 client → API gateway → ranking service ── Redis (online features, hot cache)
                │            │                    ▲
                │            ├─ ANN retrieve 500 ─┘
                │            ├─ LightGBM/DNN LTR (Triton) → policy/MMR → response
                └─ events → Redpanda/Kafka → stream features → Redis + S3 lake
 monitoring: Prometheus/Grafana; experiments: assignment service + metric store
```
Preserved: cleaner/transliterator (online query service + offline item pipeline), mood probe/line attribution (item features, explainability), BM25 (candidate source), window max-sim (snippet feature), MMR (diversity), eval harnesses (offline gates).

**Phase 1 (→100k songs, single region):** items 1–5 + minimal 10 (manifest, ANN, serialized BM25, no O(N) scans, one container). Target: p99 < 200 ms search, build < 1 day incremental, 10 QPS.
**Phase 2 (→1M users, multi-region):** items 6–9: event pipeline, Feast+Redis, two-tower + LTR on Triton, A/B, regional index replicas, audio in production.
**Phase 3 (10M+ songs):** sharded/compressed ANN (IVF-PQ, ScaNN, Milvus/Voyager), distributed + streaming online training (Monolith-style), multi-language towers, hierarchical retrieval, rights-aware multi-tenant serving.

## 5. Verdict

If only the dataset grew 100× tomorrow (≈415k songs), the order is: **(1) window vectors + O(W) matvec** — ~19 GB loaded twice, ~5.5 s/query (`window_search.py:39-42`, `mood_attribution.py:190-195,284`); **(2) the build pipeline** — ~6.2M windows / ~19 GB output vs Kaggle 9 h/20 GB limits, full-rebuild-only (`kaggle_embeddings.py:239-246`), positional IDs invalidating all artifacts (`data_audit.py:69`); **(3) BM25 startup + FAISS Flat + web-layer O(N) scans and unbounded cache** (`lexical.py:73-101`, `index.py:14`, `server.py:72,126-132`). 

Does it lack scale or scalability? **Both, in different layers.** The *algorithmic core* is professional-grade for its size — hybrid retrieval, calibrated moods, controls, evals. The *runtime data plane* is `LACKS-SCALABILITY`: one process holds the whole catalogue and every artifact, hot paths are O(N)/O(W), updates are full rebuilds on positional IDs. The *product loop* is `ARCHITECTURALLY WRONG FOR SCALE` as a recommender: zero events, zero user model, zero learned ranking, zero experimentation. The standard is **not met yet**, but the distance is one focused engineering phase, not a rewrite: the good parts are exactly what a 100k-song content recommender needs as its cold-start backbone.

## 6. Open questions / uncertainty

- Q7 audio: minimal credible path = carry `preview_url` into the catalogue (already collected: `state.py:21`, `compact.py:34`; dropped at `data_audit.py:71-80`), batch 30 s previews through MERT (acoustic) and LAION-CLAP (text-audio joint space), store vectors in MinIO, fuse by concatenation or score blending, index with text. Lyrics cannot represent melody/timbre, instrumentals, covers/versions, vocal emotion, or query-by-humming; CLAP lets mood/style queries ("sad acoustic guitar") bypass the Nepali encoder, and audio similarity clusters the catalogue independently of lyrics quality. Later: lyrics-informed audio embeddings (LIE-style) and synced-lyrics karaoke (LRCLIB `synced` flag already captured, `state.py:36`).
- I did not run the full query path with models loaded, so end-to-end p50/p99 under concurrency is inferred; the window matvec was timed in isolation.
- Extrapolations assume homogeneous song length (14.9 windows/song); a longer tail makes window counts 1.5–2× worse.
- "100×" = ~415k songs; the 1M/10M rows project the same constants.
- The word limit forces gaps to share rows; e.g. transliterator decode cost/query is omitted as not first-order.
