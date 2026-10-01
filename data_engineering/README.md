# data_engineering — dataset contracts & validation

Every committed dataset in ProjectR has a declared contract in
`data_engineering/schemas.py`: column dtypes, nullability, allowed values,
ranges, patterns and keys, tagged with a schema version.

## Validate everything

```bash
python scripts/validate_datasets.py            # skips missing datasets
python scripts/validate_datasets.py --strict   # missing dataset = failure
python -m data_engineering.validate --schema cleaned_lyrics music_rec_artifacts/cleaned_lyrics.csv
```

The full report is written to `music_rec_artifacts/data_contracts_report.json`
and a nonzero exit means a contract was breached. CI runs both the contract
tests and the production validation on every push that touches a dataset.

## Contracts today (v1)

| Dataset | File | Key |
|---|---|---|
| `cleaned_lyrics` | `music_rec_artifacts/cleaned_lyrics.csv` | `song_id` |
| `corpus_rows` | `CSVs Dataset/corpus_final_v3.csv` | — |
| `mood_labels` | `R_data/raw/gemini/*/labels_merged.csv` | `song_id` |
| `sentiment_scores` | `music_rec_artifacts/sentiment_scores.csv` | `song_id` |
| `audio_tracks` | `R_data/audio/audio_tracks.csv` | `track_key` |
| `audio_manifest` | `R_data/audio/audio_manifest.csv` | `audio_name` |
| `audio_track_matches` | `R_data/audio/audio_track_matches.csv` | `track_key` |
| `audio_new_songs` | `R_data/audio/audio_new_songs_v2.csv` | `audio_song_id` |

## Rules

1. **Bump `version`** in `schemas.py` whenever a contract changes; update this
   table and the affected producers in the same pull request.
2. **New dataset** = new schema + validator test + registry entry in
   `scripts/validate_datasets.py` + CI path filter.
3. **Fail closed**: producers should run the validator (`validate_frame`) after
   writing a dataset; a breach must not reach a commit or a publish.
4. **No silent drops**: dedup/removal decisions are recorded in a report
   (quarantine, merge mapping, duplicate candidates) and referenced from the
   commit that applies them.

## Serving artifact manifest (DE2)

`music_rec_artifacts/artifact_manifest.json` pins the serving set: canonical
SHA-256 and size for every artifact, row counts / shapes / dtypes, the schema
version each dataset was validated against, the provenance inputs, and the
config knobs used to build it. Text files are hashed with CRLF normalised to
LF, so the same manifest verifies on Windows and Linux checkouts.

```bash
python scripts/build_artifact_manifest.py   # rebuild after any artifact change
python scripts/verify_artifacts.py          # CI gate: hashes + consistency
```

Verify re-measures every file and re-runs the cross-artifact checks (song rows
agree across lyrics/ids/embeddings/probe/index, window owners stay in range,
audio vector counts agree, feature/probe/index dimensions line up). Missing
optional artifacts — the window and audio vectors are large regenerable files
not kept in git — warn; hash, schema-version or consistency drift fails.
Rebuild the manifest in the same commit as any artifact change.

## Versioned publish (DE2)

```bash
python scripts/publish_artifacts.py            # snapshot staging, flip the pointer
python scripts/publish_artifacts.py --list     # versions + which one is current
python scripts/publish_artifacts.py --dry-run  # build/check the manifest only
python scripts/publish_artifacts.py --keep 3   # retention (default 3 versions)
```

Publishing snapshots the staging set into
`music_rec_artifacts/versions/<version-id>/` (the copy is verified against its
own manifest before it becomes visible), then swaps `music_rec_artifacts/
current.json` with a single atomic replace. Serving resolves artifact paths
through the pointer — a reader sees the old version or the new one, never a
half-written set. Offline producers (`run_music_rec.py`, probe training,
corpus rebuilds/merges, the incremental updater) call
`music_rec.config.force_staging()` so their reads and writes never touch a
published version.

Versions and `current.json` are deploy state and gitignored; a fresh checkout
serves from the staging layout until its first publish. Roll back with:

```bash
python scripts/rollback_artifacts.py --list           # versions + current
python scripts/rollback_artifacts.py --previous       # newest non-current
python scripts/rollback_artifacts.py --to <version> --verify
```

Rollback is an atomic pointer swap against a retained version (nothing is
copied or moved); `--verify` hash-checks the target first. Retention keeps the
newest `--keep` versions (default 3) and never prunes the current one.

## Pipeline runner (DE3)

```bash
python scripts/pipeline.py graph
python scripts/pipeline.py run --select features --force
python scripts/pipeline.py run --select publish.artifacts
python scripts/pipeline.py run --select corpus.v3 --downstream --dry-run
python scripts/pipeline.py history --limit 5
```

Assets materialize from their declared outputs: a re-run skips steps whose
outputs already exist (`--force` re-runs them, `--backfill` forces the selection
and its descendants). Runs are recorded in `R_data/state/runs.sqlite` with
per-asset status, duration and metadata; stdout/stderr tee to
`R_data/state/logs/<run_id>/<asset>.log`. The graph (names, deps, outputs) is
defined in `pipelines/definitions.py`; design and semantics in
`docs/DE3_ORCHESTRATION_PLAN.md`.

## Roadmap

`docs/DATA_ENGINEERING_PLAN.md` tracks the phases. DE1 is the contract layer;
DE2 is in progress (manifest + verify landed, pointer-based versioned publish
next); then DE3 orchestration, DE4 queue and identity, DE5 monitoring, DE6
incremental/streaming.
