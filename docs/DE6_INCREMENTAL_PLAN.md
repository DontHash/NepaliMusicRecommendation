# DE6 — Incremental & streaming plan

Status: done — DE6a `5737399` (incremental append + watermark), DE6b `82fcbae` (events API + store + health feed), DE6c (`docs/DE6_STREAMING_SPIKE.md`). Phase DE6 of `docs/DATA_ENGINEERING_PLAN.md`.

## 1. Goal

Stop rebuilding for new data and start the feedback loop: an append-only
incremental path for corpus growth, a validated events API for impressions and
clicks, and a documented streaming path for when volume justifies it.

## 2. Current state

- `scripts/audio/update_text_artifacts.py` already implements the *prototype*
  incremental updater (append embeddings/windows/scores for new rows only), but
  it is script-shaped, not callable from the pipeline, and writes no watermark.
- The serving corpus grows through the DE3 asset graph; a one-song addition
  currently implies re-running the updater by hand.
- There is no user-event capture: no impressions/clicks, no feedback data, no
  retention policy.

## 3. Design

### DE6a — incremental append as a library + watermark

- `music_rec/incremental.py`: `append_new_songs(config, *, encoder=None,
  rebuild=True)` extracts the prototype logic:
  - prefix check (existing ids must equal the corpus prefix; refuse otherwise),
  - encode only the new tail (injectable `encoder` for hermetic tests),
  - probe-score the new rows, append embeddings/windows/ids/scores atomically,
  - rebuild features + index (skip with `rebuild=False` in tests),
  - write `R_data/state/watermarks.json` (`corpus.append`: rows, new songs,
    digest, timestamp).
- `scripts/audio/update_text_artifacts.py` becomes a thin CLI over it; the DE3
  `corpus.refresh` asset calls the library directly.
- Acceptance: adding one song touches only the new tail — existing rows are
  byte-identical after the append (tested).

### DE6b — events API + table + validation + retention

- `web_app/events.py`: `events.sqlite` at `R_data/state/events.sqlite`
  (override `PROJECTR_EVENTS_DB`), one `events` table
  (`ts, session_id, user_id, event_type, song_id, query, rank, metadata_json`),
  batch inserts in one transaction, `validate_event()` with an explicit allowed
  schema, `prune_events(keep_days=90)`, `event_stats()`.
- `POST /api/events` accepts `{"events": [...]}` (1–200 per batch), validates
  each row, returns accepted/rejected with reasons; a startup prune enforces
  retention. Privacy: no PII is expected; session ids are client-random and the
  docs state the retention window.
- `data_engineering/health.py` gains an events-feed section (rows, last event
  age, 24h counts) so the health report also covers freshness per feed.

### DE6c — streaming spike

- `docs/DE6_STREAMING_SPIKE.md`: when to move off SQLite (volume thresholds),
  Kafka/Redpanda topic design, sink options, stream-feature sketch, retraining
  triggers and the cost/benefit boundary.

## 4. Acceptance gates

- incremental: one appended song updates only the tail (prefix byte-identical),
  watermark recorded, prefix mismatch refuses, no-op is a no-op;
- events: valid batch lands (one transaction), invalid rows are rejected with
  reasons, retention delete works, stats/health freshness reports the feed;
- spike doc exists with concrete thresholds and a migration path.

## 5. Commits

- `DE6a` incremental library + pipeline action + tests
- `DE6b` events API + table + validation + health feed + tests
- `DE6c` streaming spike doc + phase status updates
