# ProjectR — Executive Audit: Gaps vs Real-World Music Recommenders

**Date:** 2026-10-01
**Method:** 7 parallel evidence-based audits (retrieval/ranking, models/MLOps, data engineering, serving/production, evaluation/testing, scalability/industry architecture, product/UX/signals). Every finding cites file:line in the track reports under `audit/`. Load-bearing claims were independently re-verified against source (see Appendix B).

---

## 1. Executive summary

ProjectR is not a toy. The **algorithmic core is genuinely professional for its size**: a real two-stage retrieve→rerank funnel, hybrid BM25+dense retrieval built for verbatim Devanagari lyrics, window-level max-similarity, a mood probe with calibrated per-line attribution, a transliterator with a layered backoff and regression gates, and an evaluation culture that documents negative results. The 4,157-song corpus is small but was collected and cleaned with unusual care.

The gap to Spotify/YouTube-class systems is **not one gap, it is four different kinds**, and conflating them is the main risk in the current roadmap:

| Layer | Verdict | Meaning |
|---|---|---|
| Algorithmic quality | **Lacks scale** (mostly) | The right shapes are there; they need in-domain training, learned ranking, and real labels — all data/loop problems. |
| Runtime data plane | **Lacks scalability** | Exact O(N)/O(W) hot paths, in-memory indexes rebuilt per process, whole-corpus loads, positional IDs, full rebuilds. Breaks at ~100k songs, not 1M. |
| Product & learning loop | **Architecturally missing** | Zero user signals logged, zero personalization, zero experimentation. More scale would not fix this; it is the actual ceiling. |
| Data platform & ops | **POC-grade plumbing** | No orchestration, contracts, provenance, CI, containers, artifact registry, observability, or rights metadata. Standard, incremental fixes. |

**Answer to the user's standard — "professional work that only lacks scale, not scalability":** that standard is **not met yet, but the distance is one focused engineering phase, not a rewrite.** The parts that would make a 100k-song content recommender work as a cold-start backbone (lyrics understanding, mood, hybrid retrieval, transliteration) already exist and are better than typical. What is missing is the data plane, the feedback loop, and production hygiene. A useful test: today, *adding one song* requires a full corpus rebuild, re-embed, re-probe, and re-index (positional `song_id`, `data_audit.py:69`); *a new machine* cannot even reproduce the eval numbers (1.27 GB of gitignored artifacts, no registry, unpinned deps); and *no user interaction is recorded anywhere* (`server.py:30,68`). Those three sentences should be false before "only lacks scale" is claimed.

**The single highest-leverage change is not a model.** It is instrumenting the product loop (anonymous impressions/clicks/skips/queries), because every learned-ranking, personalization, and online-evaluation improvement depends on it, and it is an S-effort change today.

---

## 2. What is already professional-grade (protect and build on it)

1. **Two-stage retrieval with an evidence-gated hybrid.** Dense window search + BM25 + phrase bonus, fusion disabled for mood keywords *because an eval showed a regression* (`lexical.py:191-216`; dense-only lyric nDCG@10 0.258 → hybrid 0.922, `eval_v2_report.json`). The gate is the sign of a real evaluation culture.
2. **Window max-similarity** for long lyrics (`window_search.py:34-42`) — the correct fix for mean-pool dilution, validated against a dense control.
3. **Roman↔Devanagari query handling** as a first-class path: transliterator + mined lexicon + context bigram resolver + English gate (`lyrics_pipeline/transliterator.py`). No consumer music app solves Nepali script-mixing this well; it is a genuine moat.
4. **Mood explainability that industry does not have at line level**: per-line joy/sadness/anger from window probing (`mood_attribution.py:245-276`), LOOCV-calibrated aggregation (`check_line_attribution.py:253-277`), mood-space neighbors, Nepali mood phrases. Novel, and directly usable as ranking features later.
5. **Collector engineering**: SQLite WAL queue, content-addressed HTTP cache, retries/jitter/Retry-After, per-host rate limits, circuit breaker, hashed compaction snapshots (`data_collection/`). Solid for one machine.
6. **Eval discipline**: dense/fusion controls, hard non-verbatim query set, teacher/gold holdouts, a documented negative result (muRIL collapse, `music_rec/KAGGLE.md:57-64`), and nonzero-exit transliteration gates.
7. **Serving pragmatism**: ONNX query encoder with a parity gate before adoption (~2.4 s/0.02 s vs ~14 s/0.2 s), shared model singleton, lexical fallback while cold, documented GPU/WebGL contention fix.

---

## 3. The gap vs real systems

| Capability | Real systems (Spotify/YT/Apple/TikTok class) | ProjectR today | Verdict |
|---|---|---|---|
| Content understanding | Audio (CLAP/MERT/Music2Vec) + lyrics + metadata fused; text-audio shared space | Lyrics only; off-the-shelf mpnet, not fine-tuned; mood probe is a linear head | **Data/algorithm scale** |
| Candidate generation | Multiple sources (CF, two-tower, ANN, trending, editorial) | BM25 + window dense + flat FAISS; no CF | **Scale + algorithm** |
| Ranking | Learned LTR (GBDT/DNN), multi-objective, business rules | Hand-weighted fusion + MMR constants | **Algorithm + missing labels** |
| Personalization | User embeddings from history/playlists/skips; session-aware | None; identical results for every user | **Architecturally missing** |
| Feedback loop | Impression/click/skip/dwell events → streaming features → retrain in hours/days | Nothing logged | **Architecturally missing** |
| Exploration | Bandits/exploration to break filter bubbles | None | **Missing** |
| Evaluation | Online A/B + interleaving + counterfactual; pooled human judgments; CIs | Offline proxy queries, near-tautological lyric gold, no CIs, no CI gates | **POC-grade measurement** |
| Catalogue identity/metadata | ISRC/MBID, popularity, freshness, genre, language, rights/territory | `song_id,title,artist,category,lyrics`; ISRC/preview_url collected then dropped (`data_audit.py:71-80`) | **Data + platform** |
| Serving | Multi-replica stateless services, feature store, Redis, autoscaling, SLOs | One uvicorn process, in-process CPU inference, unbounded caches | **Scalability + prod** |
| Data platform | Orchestration, lakehouse, contracts, lineage, label ops | 7+ manual CLI steps; bespoke migrations; unreproducible labels | **POC-grade plumbing** |
| Rights/compliance | Licensed catalogues, territory rules, takedown flows | Scraped lyrics in git and on Kaggle, no license file | **P0 risk** |

---

## 4. Scale vs scalability verdict, by layer

- **Algorithmic core — LACKS SCALE.** The retrieval skeleton is right and measured, but the headline nDCG 0.922 is a *verbatim-line retrieval-feasibility* score (relevance = the source song only, `queries.py:80-92`), not evidence of recommendation quality. Seed/"more like this" is nDCG 0.156, MMR diversity 0.131. These need in-domain embedding training, graded judgments, and learned ranking — data problems, not architecture.
- **Runtime data plane — LACKS SCALABILITY.** Measured today: window matvec 27–55 ms/query, BM25 build 3.2–6.7 s, lexical process ~247 MB, window vectors 182 MB loaded **twice** (recommender + attributor). At 100k songs: window scan ~1.3 s and ~4.6 GB per copy; at 1M: ~13 s and 46 GB; Kaggle rebuild exceeds its 9 h/20 GB envelope near 200k (`track-6`). `IndexFlatIP`, per-process BM25 and fuzzy n-gram map, O(N) pandas scans on every keystroke (`server.py:126-132`), and positional `song_id` (any insert invalidates every artifact) are the concrete breakpoints.
- **Product & learning loop — ARCHITECTURALLY MISSING.** No events, no user model, no exploration, no experimentation. This is not a scale problem; adding 100× data changes nothing without it.
- **Serving & ops — POC-GRADE.** Single process (`run_web_app.py:36`), uncapped inputs (`server.py:120-122,177-182`), unlocked cold-start singletons, no auth/rate limiting, no CI/containers/registry, stored-XSS via `innerHTML` of scraped titles/artists (`app.js:436,553` — verified), `print`-based observability, 1.27 GB of artifacts that a new machine cannot obtain reproducibly.
- **Evaluation — POC-GRADE, honestly built in pieces.** Rubrics, holdouts and controls are above average; the headline metrics are not trustworthy yet: mood "relaxed accuracy 0.789" is scored by a definition under which a degenerate always-both predictor scores ~0.99 (definition verified, `mood_gold_eval.py:58-71`); mood retrieval's human `gold_hit@10 0.273` is structurally 0 for the 7 of 11 queries mapped to `positive` because gold only loads joy/sadness/anger (`mood_retrieval_eval.py:82-83`); guide §14 metrics disagree with committed artifacts (coverage ~0.25 vs 0.0635, diversity ~0.25 vs 0.1311 — verified); no CIs anywhere; no CI gates.
- **Data platform — BOTH.** Great single-operator foundations; no orchestration, concurrency-safe claiming, DLQ, data contracts, label provenance, canonical identity (ISRC dropped, `datasketch` unused), lineage, or monitoring. 27k enumerated candidates sit stranded; LRCLIB artist harvest yielded 0 records for all 586 artists.
- **Product shell — gaps scale won't fix.** No playback/listen handoff, love/save/playlist/history, home/onboarding, deep links, matched-lyric snippets, suggestions/filters, mobile affordance for the core explanation, or accessibility (zero ARIA; emotion by color only). The differentiated engine is invisible in the user loop.

---

## 5. Consolidated P0 register (fix first)

| # | P0 | Evidence | Track |
|---|---|---|---|
| 1 | Instrument user signals (impressions/clicks/skips/queries, anonymous ID, no pasted text) — prerequisite for everything learned | no events anywhere; `server.py` logs only exceptions | 1,5,6,7 |
| 2 | Stop reporting inflated/stale metrics: fix mood relaxed metric + gold mapping, add base rates/CIs, correct guide §14 | verified above | 2,5 |
| 3 | Artifact manifest + startup preflight + pinned deps/model revisions + `fetch_artifacts --verify` | `config.py:81-91`, gitignored 1.27 GB | 2,4 |
| 4 | CI gates: pytest + transliteration/probe/ONNX parity + retrieval smoke on cached artifacts | no `.github/` | 2,4,5 |
| 5 | Serving hardening: input caps/timeouts, lock lazy singletons, retryable warmup, `/healthz` `/readyz` `/version`, escape DOM injection, bound payload cache | `server.py:72,88-117,120-122,177-182`; `app.js:436,553` | 4 |
| 6 | Make the mood probe reproducible (correct default label file + sidecar metadata: data/label sha, teacher, seed, metrics) | `train_mood_probe.py:37-40` defaults to superseded Qwen labels | 2 |
| 7 | Rights/takedown decision: stop redistributing full lyrics (git + Kaggle), add LICENSE/NOTICE, evaluate licensed API for the product path | `requirements`, Kaggle dataset, no license file | 3 |

---

## 6. Roadmap (each phase has a falsifiable exit criterion)

**Phase 0 — Truth & hygiene (≈1–3 weeks, S/M).** Items P0 1–7 above. *Exit:* every number in the guide reproduces from committed fixtures in CI; a fresh machine can `fetch_artifacts --verify` and serve; the server cannot be trivially DoS'd or XSS'd.

**Phase 1 — Scale-proof to 100k songs, single region (≈1–2 months, M).**
- ANN for songs and windows (HNSW/IVF-PQ or Voyager), two-stage window→song refinement; serialize BM25 + fuzzy map instead of per-process rebuild; memory-map per-song window slices for the attributor.
- Remove O(N) hot paths (cached normalized metadata, FTS/OpenSearch for title/artist, query→embedding cache).
- Canonical identity: carry ISRC/MBID through compaction, content hashes, alias-swap index updates; MinHash/LSH near-dup queue with human review (use the already-declared `datasketch`).
- Orchestrator (Dagster/Prefect) around existing scripts as data assets; MLflow registry + model cards; lakehouse-style versioned Parquet; data-contract expectations in CI.
- Queue hardening: atomic claim/lease, DLQ, page retries; best-version merge instead of first-write-wins; language-ID instead of the 2-token romanized heuristic; storefront-aware enumeration (`country=NP`).
- Container + multi-worker serving, `/readyz` probes, Prometheus metrics, structured logs.
*Exit:* p99 search < 200 ms at 100k songs; adding/removing a song is an incremental update; a corpus rebuild is a one-command DAG with lineage; CI blocks regressions.

**Phase 2 — Learning loop & product (≈2–4 months, M/L).**
- Telemetry (P0 #1) → thumbs/"mood right?" feedback → offline replay; interleaving harness (far more sensitive than A/B at low traffic) and bootstrap CIs; pooled graded judgments replacing the verbatim source-line gold.
- Learned re-ranker (LightGBM/LambdaMART) over the existing top-50 candidate features — window max-sim, BM25, fusion, sentiment alignment, token overlap, metadata — then a two-tower user model + Feast/Redis features once events exist.
- In-domain contrastive fine-tuning of the text encoder with hard negatives (the biggest single retrieval-quality lever).
- Mood-intent classifier feeding `target_sentiment`; popularity/freshness/year/genre/language metadata.
- Product: matched lyric snippet + "why" explanation, suggestions/filters/did-you-mean, deep links, zero-result recovery, WCAG 2.2 AA + mobile, mood radio + outbound listen handoff, home/onboarding.
*Exit:* ranking improves on a held-out human-judged pool with CIs; every deploy is A/B-able; a first-time mobile user can search, understand, and act.

**Phase 3 — Audio & scale (6+ months, L).**
- Carry `preview_url` (already collected, dropped at audit) → MERT/CLAP embeddings → fuse with text; enables instrumental/timbre/melody similarity, text-audio mood queries, and lyrics-independent clustering; synced lyrics (already captured) for karaoke.
- Streaming event features, sharded/compressed ANN, multi-region replicas, multi-language towers.

---

## 7. Top 10 improvements, ranked by impact/effort

1. **Signal instrumentation** (S) — start the loop.
2. **Honest metrics + CIs + CI gates** (S/M) — fix mood scoring/gold mapping, add bootstrap CIs, pin and preflight artifacts.
3. **Serving hardening** (S) — caps, locks, health/readiness, XSS escape.
4. **Artifact manifest/registry + pinned deps + fetch script** (S/M) — reproducible machine and evals.
5. **ANN + serialized lexical index + two-stage window retrieval** (M) — removes the 100k cliff.
6. **Canonical IDs + incremental index updates + near-dup review** (M) — makes the corpus growable.
7. **Orchestrator + data contracts + label provenance** (M) — turns scripts into a platform.
8. **Learned re-ranker on logged events** (M) — replaces hand weights; unlocks personalization.
9. **In-domain contrastive fine-tune of the embedding** (L) — biggest content-quality lever short of audio.
10. **Product loop: lyric snippets, search UX, a11y/mobile, mood radio + listen handoff** (M) — makes the differentiated engine visible and usable.

---

## 8. What not to do

- **Do not scale the corpus before identity and incremental updates.** Positional IDs turn every song into a global rebuild; you will pay compounding artifact debt.
- **Do not train a ranker before logging impressions.** It has no labels; you will fit the 40-query proxy and mistake it for progress.
- **Do not rebuild the model stack.** The transilterator/mood/hybrid core is the moat; the work is contracts, indexes, and the loop around it.
- **Do not invest further in the 3D donut before a11y/mobile and snippets.** The engine is ahead of its shell; users cannot yet see why a result matched.
- **Do not chase audio before the rights decision.** Audio is the biggest content gap, but scraped-lyrics legality is the bigger existential one.

---

## Appendix A — Track reports

| # | Report | Core verdict |
|---|---|---|
| 1 | `track-1-retrieval-ranking.md` | Quality lacks scale; serving also lacks scalability. |
| 2 | `track-2-models-mlops.md` | LACKS-SCALE + PROD-GAP; one stale artifact can silently corrupt every recommendation. |
| 3 | `track-3-data-engineering.md` | Both scale and scalability; standard S–M plumbing, not a dead end. |
| 4 | `track-4-serving-production.md` | Polished single-user app; cannot be safely exposed or reproduced off the author's machine. |
| 5 | `track-5-eval-testing.md` | Honest in pieces, POC-grade overall; headline retrieval number is near-tautological, no online eval, no CI. |
| 6 | `track-6-scalability-industry.md` | Algorithmic core strong; data plane unscalable; product loop architecturally missing. |
| 7 | `track-7-product-ux-signals.md` | Engine differentiated; shell is a demo; zero signal capture, no playback/library/a11y. |

## Appendix B — Independent verification log

| Claim | Verified how | Result |
|---|---|---|
| Relaxed accuracy is lenient (always-both ~0.99) | Read `mood_gold_eval.py:58-71`: mixed gold accepts either polarity; neutral requires both zero | Confirmed |
| Guide §14 metrics stale | `eval_report.json`: diversity 0.1311, coverage 0.0635, coherence 0.9121 vs guide ~0.25/0.25/0.94 | Confirmed |
| Mood retrieval gold structurally 0 for positive queries | `mood_retrieval_eval.py:82-83` loads only joy/sadness/anger gold; weak sets include `positive` | Confirmed |
| Stored-XSS via scraped metadata | `app.js:436,553` interpolate `item.title`/`item.artist` into `innerHTML` | Confirmed |
| ISRC / preview_url dropped before corpus | Present in `data_collection/state.py:21-22`, `compact.py:34`; absent in `data_audit.py:71-80` output schema | Confirmed |
