# DE5 — Monitoring & quality observability plan

Status: done — DE5a `af874e2` (metrics stream + data health), DE5b (`/metrics` endpoint + CI health gate). Phase DE5 of `docs/DATA_ENGINEERING_PLAN.md`.

## 1. Goal

Know when data drifts, a feed goes stale or a rebuild fails — without reading
logs: structured run metrics, a green/red data-health report with quality
budgets and freshness, and a Prometheus `/metrics` endpoint.

## 2. Current state

- The DE3 runner already records runs/assets in `R_data/state/runs.sqlite`
  (status, duration, metadata), but nothing emits a metrics stream and nothing
  evaluates data quality over time.
- DE1 validates *schema* per dataset; there are no row-count/duplication/
  coverage/freshness budgets and no row-delta history.
- The web app exposes functional endpoints only.

## 3. Design

### DE5a — metrics stream + data health

- `pipelines/metrics.py`: `MetricsWriter` appends one JSON line per event to
  `R_data/state/metrics.jsonl`; the runner emits `kind="asset"` (run_id, asset,
  status, duration_s, message) and `kind="run"` (status, assets, duration).
- `data_engineering/health.py`: per-dataset metrics, budgets, freshness and row
  deltas vs the previous snapshot (`R_data/state/health_history.jsonl`), plus an
  artifact-manifest consistency check and an optional events-feed section.
- `scripts/data_health.py`: green/red table, JSON report at
  `music_rec_artifacts/data_health_report.json`, nonzero exit on a red dataset;
  `--strict` (missing dataset fails), `--fail-on-stale`, `--no-history`.

**Budgets** (calibrated against the current corpus; margins chosen so the gate
catches real regressions without flapping):

| Dataset | Budgets |
|---|---|
| `cleaned_lyrics` | rows ≥ 4000 · duplicate-lyrics share ≤ 0.02 · empty artist ≤ 0.02 · empty title ≤ 0.005 · avg tokens ≥ 50 · min tokens ≥ 10 |
| `corpus_rows` | rows ≥ 4000 · sources ≥ 5 |
| `sentiment_scores` | rows ≥ 4000 · coverage vs cleaned ≥ 0.999 |
| `mood_labels` | rows ≥ 3000 |
| `audio_tracks` / `audio_track_matches` / `audio_file_map` | rows ≥ 3000 |
| `audio_track_matches` | matched share (`match_song_id` or `new_id`) ≥ 0.20 |
| `audio_new_songs` | rows ≥ 10 |
| artifacts | manifest present and internally consistent |

Freshness: dataset age ≤ 30 days (labels/audio 90) is a warning by default and
fails with `--fail-on-stale`; CI checkouts are fresh by construction.

### DE5b — `/metrics` + CI gate

- `web_app/metrics.py`: renders Prometheus text from the run store, the health
  report, the events database and the published-artifact pointer; tolerant of
  missing files. The server exposes it at `GET /metrics` with a short TTL cache.
- CI: `scripts/data_health.py` runs in the data-contracts workflow after the
  dataset validation, so a budget breach fails the build.

## 4. Acceptance gates

- runner tests assert `metrics.jsonl` rows (asset + run) and that dry runs emit
  nothing;
- health tests: green tree passes; a duplicate-share or row-count breach turns
  red; deltas are computed from history; stale freshness is flagged;
- `/metrics` renders run counters, dataset rows/age, event counters and the
  artifact version from hermetic fixtures;
- CI: health step fails on a deliberate budget breach (tested hermetically).

## 5. Commits

- `DE5a` metrics stream + data health + tests
- `DE5b` `/metrics` endpoint + CI gate + docs
