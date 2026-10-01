# DE6 streaming spike: from the SQLite event store to a real bus

Status: spike — not implemented. This document records the trigger thresholds,
the target shape and the migration path so the decision is deliberate rather
than accidental.

## 1. When to move off the SQLite store

Current design (`web_app/events.py`): one WAL SQLite file, batch inserts in a
single transaction, 90-day retention, validated rows. That is the right choice
while all of the following hold:

- writers are a single serving process (or a few in one host);
- volume is below roughly **5M events/month** and **~50 events/s peak**;
- consumers are batch jobs (health, metrics, offline evals) that can read the
  same file.

Move when any of these becomes true:

- several serving replicas (or separate hosts) must write the same feed;
- sustained write rate approaches SQLite's WAL ceiling (a few hundred writes/s
  with contention);
- near-real-time features (session intent) or automated retraining triggers are
  required;
- the event stream must survive the serving host (durability/DR).

## 2. Target shape

```
producer (web app batch endpoint)
   └─ topic  projectr.events            key: session_id (fallback song_id)
             partitions: 6              retention: 7 days
   └─ sink consumer (batch 1k / 5s)
             ├─ Postgres/ClickHouse table  events (dedupe on event_id)
             ├─ stream processor           session features (windowed)
             └─ invalid rows               topic projectr.events.dlq
```

Selected bus: **Redpanda** (Kafka-compatible, single binary, no ZooKeeper) so
the code path is standard Kafka if managed hosting is preferred later.

Schema evolution: every event carries `event_id` (producer UUID),
`schema_version`, and the current validated fields (`ts`, `session_id`,
`user_id`, `event_type`, `song_id`, `query`, `rank`, `metadata_json`). The
sink upserts on `event_id`, which makes retries idempotent. Validation mirrors
`web_app/events.validate_event`; rejects go to the DLQ topic with the reason.

## 3. Migration path (keep it boring)

1. Add `event_id` + `schema_version` to the SQLite writer and API (backward
   compatible; client-provided or generated server-side).
2. Stand up single-node Redpanda (docker) and create `projectr.events` +
   `projectr.events.dlq`.
3. Dual-write from the API: SQLite remains the read path; a background producer
   publishes batches to the topic with at-least-once semantics.
4. Build the sink consumer and switch reads (metrics, health, features) to the
   sink; keep SQLite as the dev fallback behind the existing interface.
5. Remove dual-write once the sink is authoritative and dashboards have moved.

## 4. Stream features and retraining triggers

- Windowed session features (5/30-minute tumbling): impressions, clicks,
  skips, query strings → a `session_intent` table joined at request time.
- Daily job: if new click events ≥ N, schedule the ranking eval and (when the
  drift gates in DE5 stay green) a retrain; otherwise no-op.
- Impression/click logs power unbiased evaluation later (position-bias aware
  metrics), which is the main long-term reason to collect them at all.

## 5. Cost/benefit

Redpanda + a sink database is a small always-on VM plus operational surface.
Below the thresholds it buys nothing over the current file; above them it
removes single-writer limits, provides replay (retention), and makes the
feedback loop independent of the serving process. The dual-write step means the
switch can be rolled back at any point without data loss.
