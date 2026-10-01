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

## Roadmap

`docs/DATA_ENGINEERING_PLAN.md` tracks the phases. DE1 (this module) is the
contract layer; DE2 adds versioned publishing, DE3 orchestration, DE4 queue and
identity, DE5 monitoring, DE6 incremental/streaming.
