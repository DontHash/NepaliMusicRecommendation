"""Hermetic tests for the data-health report (budgets, freshness, deltas)."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd

from data_engineering.health import (
    Budget,
    build_health_report,
    evaluate_budgets,
    events_health,
    format_health_report,
)

SENTIMENT_COLUMNS = ["song_id", "joy", "sadness", "anger", "fear", "depression",
                     "positive", "negative", "sentiment_score", "sentiment_label"]


def _write_cleaned(path: Path, lyrics: list[str]) -> None:
    pd.DataFrame({
        "song_id": list(range(len(lyrics))),
        "title": [f"T{index}" for index in range(len(lyrics))],
        "artist": [f"A{index}" for index in range(len(lyrics))],
        "category": ["nepali"] * len(lyrics),
        "lyrics": lyrics,
        "token_count": [len(text.split()) for text in lyrics],
    }).to_csv(path, index=False, encoding="utf-8")


def _write_sentiment(path: Path, ids: list[int]) -> None:
    frame = pd.DataFrame({"song_id": ids})
    for column in SENTIMENT_COLUMNS[1:-2]:
        frame[column] = 0.1
    frame["sentiment_score"] = 0.0
    frame["sentiment_label"] = "neutral"
    frame.to_csv(path, index=False, encoding="utf-8")


def _coverage(metrics, context):
    return metrics["rows"] / max(context.get("cleaned_lyrics", {}).get("rows", 1), 1)


def _fixture(tmp_path: Path, lyrics: list[str] | None = None) -> dict[str, Path]:
    lyrics = lyrics or ["माया लाग्छ तिम्रो मन", "फेरि भेटौं कहिले", "सपनामा आउने साथी"]
    cleaned = tmp_path / "cleaned_lyrics.csv"
    sentiment = tmp_path / "sentiment_scores.csv"
    _write_cleaned(cleaned, lyrics)
    _write_sentiment(sentiment, list(range(len(lyrics))))
    return {"cleaned_lyrics": cleaned, "sentiment_scores": sentiment}


def _budgets() -> dict[str, list[Budget]]:
    return {
        "cleaned_lyrics": [
            Budget("rows", minimum=3),
            Budget("duplicate_lyrics_share", maximum=0.1),
            Budget("empty_artist_share", maximum=0.1),
        ],
        "sentiment_scores": [
            Budget("rows", minimum=3),
            Budget("coverage", minimum=0.999, derive=_coverage),
        ],
    }


def test_green_report_passes_contract_and_budgets(tmp_path: Path):
    report = build_health_report(tmp_path, _fixture(tmp_path), budgets=_budgets(),
                                 freshness_overrides={}, check_artifacts=False)
    assert report["status"] == "green", report["failed"]
    cleaned = report["datasets"]["cleaned_lyrics"]
    assert cleaned["contract"] == "pass"
    assert cleaned["rows"] == 3
    assert all(check["passed"] for check in cleaned["budgets"])
    assert report["datasets"]["sentiment_scores"]["metrics"]["rows"] == 3


def test_duplicate_share_breach_is_red(tmp_path: Path):
    duplicated = ["माया लाग्छ तिम्रो मन", "माया लाग्छ तिम्रो मन", "फेरि भेटौं कहिले"]
    report = build_health_report(tmp_path, _fixture(tmp_path, duplicated),
                                 budgets=_budgets(), freshness_overrides={},
                                 check_artifacts=False)
    assert report["status"] == "red"
    assert "cleaned_lyrics" in report["failed"]
    breach = next(check for check in report["datasets"]["cleaned_lyrics"]["budgets"]
                  if check["metric"] == "duplicate_lyrics_share")
    assert breach["passed"] is False


def test_contract_violation_is_red(tmp_path: Path):
    datasets = _fixture(tmp_path)
    frame = pd.read_csv(datasets["cleaned_lyrics"], encoding="utf-8")
    frame.loc[0, "token_count"] = 0  # schema requires >= 1
    frame.to_csv(datasets["cleaned_lyrics"], index=False, encoding="utf-8")
    report = build_health_report(tmp_path, datasets, budgets=_budgets(),
                                 freshness_overrides={}, check_artifacts=False)
    assert report["status"] == "red"
    assert report["datasets"]["cleaned_lyrics"]["contract"] == "fail"


def test_row_delta_from_history(tmp_path: Path):
    datasets = _fixture(tmp_path)
    history = tmp_path / "health_history.jsonl"
    first = build_health_report(tmp_path, datasets, budgets=_budgets(),
                                freshness_overrides={}, check_artifacts=False,
                                history_path=history)
    assert "delta_rows" not in first["datasets"]["cleaned_lyrics"]

    _write_cleaned(datasets["cleaned_lyrics"],
                   ["माया लाग्छ तिम्रो मन", "फेरि भेटौं कहिले", "सपनामा आउने साथी", "नयाँ गीत"])
    _write_sentiment(datasets["sentiment_scores"], [0, 1, 2, 3])
    second = build_health_report(tmp_path, datasets, budgets=_budgets(),
                                 freshness_overrides={}, check_artifacts=False,
                                 history_path=history)
    assert second["datasets"]["cleaned_lyrics"]["delta_rows"] == 1


def test_stale_flag_and_fail_on_stale(tmp_path: Path):
    datasets = _fixture(tmp_path)
    old = 1_600_000_000
    os.utime(datasets["cleaned_lyrics"], (old, old))
    report = build_health_report(tmp_path, datasets, budgets=_budgets(),
                                 max_age_days=1.0, freshness_overrides={},
                                 check_artifacts=False)
    assert report["datasets"]["cleaned_lyrics"]["stale"] is True
    assert report["status"] == "green" and "cleaned_lyrics" in report["stale"]

    failed = build_health_report(tmp_path, datasets, budgets=_budgets(),
                                 max_age_days=1.0, freshness_overrides={},
                                 check_artifacts=False, fail_on_stale=True)
    assert failed["status"] == "red"


def test_missing_dataset_strictness(tmp_path: Path):
    datasets = _fixture(tmp_path)
    datasets["audio_tracks"] = tmp_path / "missing.csv"
    lenient = build_health_report(tmp_path, datasets, budgets=_budgets(),
                                  freshness_overrides={}, check_artifacts=False)
    assert lenient["status"] == "green"
    assert lenient["datasets"]["audio_tracks"]["status"] == "missing"

    strict = build_health_report(tmp_path, datasets, budgets=_budgets(),
                                 freshness_overrides={}, check_artifacts=False, strict=True)
    assert strict["status"] == "red"
    assert "audio_tracks" in strict["failed"]


def test_events_health_reports_feed(tmp_path: Path):
    assert events_health(tmp_path / "absent.sqlite")["status"] == "absent"

    db = tmp_path / "events.sqlite"
    connection = sqlite3.connect(db)
    connection.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, ts TEXT)")
    connection.execute("INSERT INTO events (ts) VALUES (datetime('now'))")
    connection.commit()
    connection.close()

    health = events_health(db)
    assert health["status"] == "present"
    assert health["rows"] == 1 and health["last_24h"] == 1
    assert health["age_hours"] is not None


def test_evaluate_budgets_reports_breaches():
    checks = evaluate_budgets({"rows": 2}, [Budget("rows", minimum=5),
                                            Budget("missing", maximum=1.0)])
    assert checks[0]["passed"] is False
    assert checks[1]["value"] is None and checks[1]["passed"] is False


def test_format_health_report_mentions_rows(tmp_path: Path):
    report = build_health_report(tmp_path, _fixture(tmp_path), budgets=_budgets(),
                                 freshness_overrides={}, check_artifacts=False)
    text = format_health_report(report)
    assert "rows=3" in text and "artifacts" in text
