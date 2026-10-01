# DE3 — Orchestration plan (asset graph + runner)

Status: in progress. Phase DE3 of `docs/DATA_ENGINEERING_PLAN.md`.

## 1. Goal

Replace the manual, ordered sequence of build scripts with one dependency-aware
runner that knows the data graph, records what ran, and can resume, backfill and
retry:

```bash
python scripts/pipeline.py run --select features --force
python scripts/pipeline.py run --select publish.artifacts --downstream
python scripts/pipeline.py graph
python scripts/pipeline.py history
```

## 2. Scope / non-goals

**In:** asset graph, topological execution, selection (`--select`,
`--downstream`, `--backfill`, `--force`, `--dry-run`), output-based resume,
per-asset logs, retries, SQLite run history, external-source modelling.

**Out (later phases):** scheduling/daemon + freshness alerts (DE5), incremental
change detection (DE6), queue lease/DLQ (DE4), distributed execution. The runner
stays thin and declarative so Dagster/Prefect can wrap it without a rewrite.

## 3. Asset graph (v1)

`source` marks inputs the repository cannot regenerate (scrapes, label shards,
the local audio collection).

| Asset | Deps | Outputs |
|---|---|---|
| `corpus.source` *(external)* | — | `CSVs Dataset/Lyrics_Dataset_final.csv` |
| `corpus.clean` | corpus.source | `music_rec_artifacts/cleaned_lyrics.csv` |
| `corpus.embed` | corpus.clean | `embeddings.npy`, `embedding_ids.json`, `window_vectors.npy`, `window_owners.npy` |
| `labels.gemini` *(external)* | — | `R_data/raw/gemini/corpus_v3/labels_merged.csv` |
| `mood.probe` | corpus.embed, labels.gemini | `mood_probe.npz`, `sentiment_scores.csv`, `mood_probe_report.json` |
| `mood.vectors` | mood.probe | `mood_vectors.csv` |
| `features` | corpus.embed, mood.probe, mood.vectors | `feature_matrix.npy`, `feature_meta.json` |
| `index.songs` | features | `lyrics.faiss` |
| `index.windows` | corpus.embed | `window_index.faiss` when ANN is on |
| `audio.collection` *(external)* | — | — (external directory) |
| `audio.manifest` | audio.collection, corpus.clean | `audio_manifest.csv`, `audio_tracks.csv` |
| `audio.lyrics` | audio.manifest | `audio_lyrics.jsonl` |
| `audio.dataset_lines` | audio.lyrics, corpus.clean | `audio_track_matches.csv`, `audio_file_map.csv`, `audio_new_songs_v2.csv` |
| `audio.embeddings` | audio.manifest | `audio_embedding_keys.csv`, `audio_embeddings.npy` |
| `audio.similarity` | audio.embeddings | `audio_duplicate_candidates.csv` |
| `corpus.v3` | audio.dataset_lines, corpus.clean | `CSVs Dataset/corpus_final_v3.csv`, `merge_report_v3.json` |
| `corpus.refresh` | corpus.v3, corpus.embed | `text_artifacts_update_report.json` |
| `publish.artifacts` | features, index.songs, index.windows, mood.vectors, corpus.refresh | `artifact_manifest.json`, `current.json` |

## 4. Execution semantics

- **materialized(asset)** = every declared output exists; assets with no
  declared outputs fall back to "last recorded run was ok". Outputs are the
  state, so the first `--select publish.artifacts` does not re-embed.
- **select** runs the named assets and pulls in ancestors only when their
  outputs are missing.
- **--downstream** adds all descendants of the selection.
- **--backfill** = downstream + force the selected/descendant assets.
- **--force** re-runs everything in scope even if materialized.
- **resume**: re-invoking the same command after an interruption skips steps
  whose outputs exist (unless `--force`/`--backfill`).
- **failure**: dependents are recorded `blocked`, independent branches still
  run, the run is `failed` and the CLI exits non-zero.
- **retries**: per-asset count plus a `--retries N` override.

## 5. Run history and logs

`R_data/state/runs.sqlite` (gitignored):

- `runs(id, started_at, finished_at, status, select, options, git_sha)`
- `asset_runs(id, run_id, asset, status, started_at, finished_at, duration_s,
  message, metadata_json)` — status ∈ `ok | failed | skipped | blocked | external`

Per-asset logs are teed to `R_data/state/logs/<run_id>/<asset>.log`.

## 6. Deliverables & commits

- **DE3a** — `pipelines/core.py` (Asset/RunContext/script_action),
  `pipelines/state.py` (SQLite history), `pipelines/runner.py` (Pipeline:
  selection, topo execution, logging, retries), hermetic tests, this plan.
- **DE3b** — `pipelines/definitions.py` (the ProjectR graph and actions),
  `scripts/pipeline.py` CLI, docs, and a recorded real run.

## 7. Acceptance gates

- Graph validates: acyclic, every dep exists, external assets have no action.
- Runner tests: topo order, select/downstream/backfill/force, dependency
  blocking, retry, output-based resume, dry-run, history rows.
- Real run: `pipeline run --select features --force` and
  `pipeline run --select publish.artifacts` succeed and persist history;
  `pipeline graph` prints the DAG; `pipeline history` shows both runs.
