# ProjectR Data Engineering Plan — from script batch ETL to a platform

Status: active. Owner: project maintainer. Created 2026-10-01.

This document turns the executive-audit gaps (see `audit/00_EXECUTIVE_AUDIT.md` and
`audit/track-3-data-engineering.md`) into a phased, commit-by-commit engineering
programme. Each phase has explicit deliverables, acceptance criteria and commit
boundaries. Nothing is "done" until its gates pass in CI or a checked report.

---

## 1. Where we stand (maturity)

On a 5-level data-engineering scale (1 ad-hoc scripts → 2 repeatable batch ETL →
3 orchestrated platform with contracts/lineage → 4 incremental/streaming →
5 real-time self-serve), ProjectR is **mid-L2 with genuine L3 traits**.

| Layer | Today |
|---|---|
| Explicit ETL pipelines | 3 (corpus collection, lyrics/transliteration, audio→lyrics) + artifact materialization |
| Medallion layout | de-facto Bronze (`R_data/raw`, snapshots) → Silver (`corpus_final_v3`, `cleaned_lyrics`) → Gold (embeddings, windows, probe, features, indices) |
| Reliability | WAL work queue, cached HTTP with retry/rate-limit/circuit-breaker, resumable jobs, atomic writes in newer paths |
| Quality | cleaner + quarantine + gold/teacher separation + eval gates + (new) audio language/dedup gates |
| Provenance | `schema_version`, `git_sha`, input SHA-256, `generated_at` in reports; content-addressed `A-…` ids |
| Testing | 200+ tests incl. hermetic pipeline tests; first CI workflow |
| **Missing** | orchestration/DAG, schema registry & contracts, versioned artifact publish, lineage graph, freshness/quality monitoring, queue lease/DLQ, canonical ids (ISRC/MBID), streaming events |

## 2. Principles

1. **Contracts before code** — a dataset without a declared schema is not ingestable.
2. **Idempotent and replayable** — every step safe to re-run; inputs keyed by content.
3. **Atomic publish** — no reader ever sees half-written artifacts; publish by pointer swap.
4. **Provenance by default** — every artifact records inputs, code revision, config, schema version.
5. **Quality gates in CI** — row counts, schema, rates, drift budgets fail the build.
6. **No silent data loss** — dedup/drop decisions are recorded and reviewable.
7. **Observability** — run history, freshness, duration and failure metrics from day one.

## 3. Target architecture

```
CONTROL PLANE
  orchestrator (asset graph, backfills, retries)    run history (SQLite -> Postgres)
  contracts (schema validation)                     lineage (input hashes + run ids)
  monitoring (counts, freshness, failures)          CI quality gates

DATA PLANE
  sources ─► BRONZE ────────────► SILVER ───────────────► GOLD ─────────────► SERVING
  sites      raw pages/cache      corpus_final_v3        embeddings/windows    FastAPI
  APIs       work.sqlite queue    cleaned_lyrics         probe/sentiment       recommender
  audio      snapshots (hashed)   labels (Gemini v3)     features/FAISS        Studio
  library    audio manifests      audio track matches    CLAP audio vectors
                                        │
                             PUBLISH: versions/<artifact-id>/ + current.json pointer
```

---

## 4. Phases

### DE0 — Closure & baseline  *(1 commit)*
**Status:** done — `bcaf88d` (chunking fix), `b2b409b` (scale layer), `d8b9fa4` (corpus v3 + refresh).
**Goal:** land the in-flight corpus v3 merge + local artifact refresh + scale layer
so the platform work starts from a clean, reproducible baseline.
**Deliverables:** corpus v3 committed; probe retrained on v3 labels; embeddings/windows
regenerated with a reproducible local recipe (parity gate green); ANN + caches in
place (A10); re-baselined eval reports (`eval_v3_*`).
**Acceptance:** `check_probe_parity` PASS, `check_ann_parity` PASS, evaluator suite
green, `git status` clean.
**Commits:** `A9` merge/refresh, `A10` scale layer.

### DE1 — Schemas & data contracts  *(2 commits)*
**Status:** done — `aac4dfd` (9 schemas, validator, CI gate, 9/9 datasets valid).
**Goal:** every dataset has one declared schema and machine-validated rows.
**Workstreams:**
- `data_engineering/schemas.py`: canonical schemas (candidates, corpus rows, labels,
  audio manifest/tracks/matches, artifact manifest, events) with dtypes, nullability,
  allowed values and a `schema_version`.
- `data_engineering/validate.py`: CLI + library validation for a CSV/Parquet +
  `--schema` name; returns machine-readable report; nonzero exit on breach.
- `scripts/validate_datasets.py`: validate the whole production set in one call.
- CI job: run validation on committed datasets.
**Acceptance:** all production datasets validate; a deliberately broken row fails CI;
tests cover each schema; docs list schema versions.
**Commits:** `DE1a` schemas+validator+tests, `DE1b` CI + doc + first fixes found by
validating existing data (expected: the gappy-id/title-empty class of issue).

### DE2 — Versioned publish & artifact manifest  *(2–3 commits)*
**Status:** done — DE2a `96595d8` (manifest + verify + CI gate), DE2b `7330101` (versioned publish + pointer resolution), DE2c rollback + docs (last commit of the phase).
**Goal:** atomic, rollbackable artifact sets with full provenance.
**Workstreams:**
- `data_engineering/artifacts.py`: build manifest (path, SHA-256, size, rows, dims,
  schema_version, git_sha, input hashes, config hash); publish to
  `music_rec_artifacts/versions/<id>/`; write `current.json` pointer.
- `scripts/publish_artifacts.py` + `scripts/verify_artifacts.py` (manifest check,
  dims vs corpus, index ntotal vs rows, window owner bounds).
- `Config` resolves artifact paths through the pointer (env override
  `PROJECTR_ARTIFACTS_POINTER`); readers never open partially written versions.
- Rollback: pointer flip; document.
**Acceptance:** serving loads only published sets; verify fails on a tampered file;
rollback demonstrated in tests; predecessor version retained.
**Commits:** `DE2a` manifest+verify, `DE2b` pointer-based config + publish scripts,
`DE2c` rollback docs/tests.

### DE3 — Orchestration (asset graph)  *(2 commits)*
**Status:** done — DE3a `7093631` (runner core), DE3b (ProjectR graph + CLI).
**Goal:** replace the 7-step manual sequence with a dependency-aware runner with
run history and backfills; keep it a thin adapter so Dagster/Prefect can replace it.
**Workstreams:**
- `pipelines/assets.py`: asset definitions (`candidates.raw`, `corpus.raw`,
  `corpus.clean`, `labels.gemini`, `embeddings`, `windows`, `probe`, `features`,
  `index.songs`, `index.windows`, `audio.manifest`, `audio.lyrics`, `audio.matches`,
  `corpus.v3`, `publish.artifacts`) with deps and idempotency keys.
- `pipelines/runner.py`: topological execution, `--select`, `--to`, `--backfill`,
  retries, per-asset logs, run history in `R_data/state/runs.sqlite`.
- `scripts/pipeline.py` CLI; wrap existing scripts/functions as asset actions.
**Acceptance:** `pipeline run --select corpus.v3 --downstream publish` works from a
clean checkout; interrupted runs resume; history row per asset execution.
**Commits:** `DE3a` graph+runner+tests, `DE3b` wrap all phases + docs.

### DE4 — Queue robustness & identity  *(2–3 commits)*
**Status:** done — DE4a lease/DLQ (`0106343`), DE4b best-version merge + ISRC (`f914f05`), DE4c LSH review.
**Goal:** horizontal-safe ingestion and canonical music identity.
**Workstreams:**
- Atomic claim/lease (`UPDATE ... RETURNING` semantics in SQLite transaction), lease
  TTL + orphan reset, `failed`/`dead` statuses, DLQ export.
- Page-level retry budgets; best-version merge instead of first-write-wins.
- Identity: carry ISRC/MBID through compaction into the corpus; MinHash/LSH near-dup
  candidates (`datasketch` is already declared) with a review CSV; survivorship rules.
**Acceptance:** two concurrent fetchers never fetch the same candidate; stuck rows
auto-recover; identity report lists merge candidates with decisions recorded.
**Commits:** `DE4a` lease/DLQ, `DE4b` best-version merge, `DE4c` identity+LSH review.

### DE5 — Monitoring & quality observability  *(1–2 commits)*
**Status:** done — DE5a `af874e2` (metrics stream + data health), DE5b (`/metrics` + CI gate).
**Goal:** know when data drifts or a rebuild fails, without reading logs.
**Workstreams:**
- Structured run/asset metrics (duration, rows in/out, dropped counts, error rate)
  written to `R_data/state/metrics.jsonl` + `/metrics` in the web app.
- Freshness checks per dataset; quality budgets (exact-dup rate, artifact-line ratio,
  unknown-script share) enforced by DE1 validator.
- `scripts/data_health.py` report: freshness, row deltas vs last run, gate results.
**Acceptance:** health report shows green/red per dataset; CI fails on breached budget.
**Commits:** `DE5a` metrics+health, `DE5b` alert thresholds + docs.

### DE6 — Incremental & streaming  *(2+ commits)*
**Status:** done — DE6a `5737399` (incremental append + watermark), DE6b `82fcbae` (events API + store + health feed), DE6c (streaming spike, `docs/DE6_STREAMING_SPIKE.md`).
**Goal:** stop full rebuilds for new data; start the feedback loop.
**Workstreams:**
- Watermarked incremental append path for corpus/labels/audio (the audio updater is
  the prototype) generalised in DE3 assets.
- Event ingestion (`POST /api/events`, `events` table, batched writes) for
  impressions/clicks; retention policy; privacy note.
- Later: Kafka/Redpanda + stream features once volume justifies it; retraining
  triggers from events.
**Acceptance:** adding one song touches only the incremental assets; events land with
schema validation; health shows freshness per feed.
**Commits:** `DE6a` incremental assets, `DE6b` events API+table, `DE6c` streaming
spike doc.

---

## 5. Commit conventions

- Subject prefix `DE<n><letter?>: <what>` (e.g. `DE1a schemas: canonical dataset
  contracts + validator CLI + tests`). Existing history uses `C*`/`A*`; DE continues it.
- Body states **what changed, why, evidence** (commands + results), and any
  follow-up debt, matching the repo's established style.
- Each commit: tests or a checked report; docs updated when behaviour changes;
  datasets/artifacts touched only in commits dedicated to them.
- No mixed concerns: schema work does not ship artifact refreshes; artifact refresh
  does not ship code refactors.

## 6. Phase gates (summary)

| Phase | Gate |
|---|---|
| DE0 | parity + eval suite green; clean tree |
| DE1 | 100% of committed datasets validate; broken-row test fails CI |
| DE2 | verify detects tamper; pointer rollback test; serving rejects unpinned sets |
| DE3 | clean-checkout `pipeline run` to publish; run history recorded |
| DE4 | concurrency test: no double fetch; DLQ non-empty only for true failures |
| DE5 | health report red/green works; CI data budgets enforced |
| DE6 | one-song incremental add proven; events validated end-to-end |

## 7. Immediate order of work

1. DE0 closure — done (`bcaf88d`, `b2b409b`, `d8b9fa4`).
2. DE1 (schemas + validator + CI) — done (`aac4dfd`).
3. DE2 (manifest, publish, rollback) — done (`96595d8`, `7330101`, rollback commit).
4. DE3 (runner) — done (`7093631`, graph/CLI commit).
5. DE4 (queue lease/DLQ + identity) — done (`0106343`, `f914f05`, LSH review commit).
6. DE5 (metrics + data health + `/metrics`) — done (`af874e2`, `10e2629`).
7. DE6 (incremental append + events + streaming spike) — done (`5737399`, `82fcbae`, spike commit).

All planned phases are complete. The remaining work is volume-triggered:
streaming (see `docs/DE6_STREAMING_SPIKE.md` thresholds), queue partitioning,
and the DE5 quality budgets extended as new feeds appear.
