# DE4 — Queue robustness & identity plan

Status: done — DE4a `0106343` (lease/DLQ), DE4b `f914f05` (best-version merge + ISRC), DE4c (LSH review). Phase DE4 of `docs/DATA_ENGINEERING_PLAN.md`.

## 1. Goal

Make ingestion safe to run in parallel and give songs a canonical identity:

- **Queue**: atomic claim + lease, orphan recovery by expiry, attempt budgets,
  dead-letter status and export, for both the candidate and page queues.
- **Identity**: best-version merge at compaction (no metadata dropped), ISRC
  carried through compaction, and a MinHash/LSH duplicate review that records
  decisions.

## 2. Gaps today

| Area | Problem |
|---|---|
| claim | `next_batch` SELECT then `mark_fetching` per row: two workers can claim the same candidate; there is no owner or expiry |
| orphans | `reset_orphaned()` resets **every** `fetching` row, including rows a live worker is processing |
| budget | `max_attempts` only filters `next_batch`; exhausted candidates stay `new` forever, invisible |
| pages | same SELECT-then-`mark_page` race, no attempt counter, no lease, no dead status |
| compaction | one row wins per `artist\|title` group and siblings are dropped: album/duration/preview/ISRC lost; `isrc` is not even a compacted column |
| identity | only folded artist+title exact grouping; no near-duplicate review, no recorded merge decisions |

MBID note: no source in this project ingests MusicBrainz ids (Deezer/ITunes give
ISRC), so DE4 carries ISRC and leaves MBID to a future source addition.

## 3. Design

### DE4a — lease/DLQ

- Schema migration (`ALTER TABLE ADD COLUMN` guarded by `PRAGMA table_info`):
  `candidates` gains `lease_owner`, `lease_expires_at`; `pages` gains
  `attempt_count`, `last_error`, `lease_owner`, `lease_expires_at`.
- `claim_batch(conn, owner, limit, ...)` = one `UPDATE ... WHERE id IN (SELECT
  ...) RETURNING *` inside `BEGIN IMMEDIATE`; it increments `attempt_count` and
  stamps the lease. `claim_pages` is the same for `pages`.
- `mark_status(..., owner=...)` clears the lease and refuses (rowcount 0) to
  overwrite a row whose lease belongs to another worker; `mark_page` clears the
  lease; `save_lyrics` accepts the owner.
- `reset_orphaned(force=False)` recovers only expired/NULL leases; `force=True`
  is the explicit admin sweep. Same for pages.
- `sweep_exhausted()` moves attempt-exhausted rows to `dead`;
  `dead_letters()`/`export_dead_letters()` feed an operator CLI
  (`data_collection/queue_admin.py`: status, sweep, dlq, requeue, reset-orphans).
- `fetch.py` claims with a `--worker-id` and `--lease-seconds`; `crawl_sites.py`
  claims pages and uses `retry_page` for fetch/parse failures into the budget.

### DE4b — best-version merge + ISRC passthrough

- `compact()` keeps the ranked lyric winner per `artist|title` group but fills
  missing `album`, `duration_s`, `preview_url`, `isrc` and `source_url` from
  siblings in rank order; `isrc` is added to the compacted corpus columns.
- The report records merge decisions (kept/dropped ids, filled fields) with
  per-field counters, so survivorship is auditable instead of implicit.

### DE4c — LSH duplicate review

- `data_collection/identity.py`: MinHash + MinHashLSH (`datasketch`) over
  folded `artist title` 2-grams, exact Jaccard filter, survivorship suggestion
  from source priority + script rank.
- `data_collection/review_duplicates.py` writes
  `R_data/corpus/duplicate_review.csv` (left/right metadata, similarity,
  `suggested_action`, `decision`) and a JSON report; decisions are recorded and
  applying them stays a reviewed manual step.

## 4. Commits

- `DE4a` queue lease + DLQ + retry budgets
- `DE4b` best-version merge + ISRC passthrough
- `DE4c` identity + LSH duplicate review

## 5. Acceptance gates

- **concurrency**: two workers claiming from one database never receive the same
  candidate (threaded test with a barrier); same for pages.
- **leases**: a live lease survives `reset_orphaned()`; an expired or NULL lease
  is recovered; a non-owner `mark_status` is refused.
- **DLQ**: exhausted attempts become `dead`, export to CSV, and requeue with
  attempts reset works.
- **merge**: a duplicate group keeps the best lyrics but preserves sibling
  metadata; ISRC appears in `corpus_raw.csv`; the report records the decision.
- **review**: spelling-variant songs pair up, unrelated songs do not, output is
  deterministic and carries a `decision` column.
