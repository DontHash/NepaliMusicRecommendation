"""Content-addressed artifact manifest for the serving layer.

The manifest is the contract between producers (rebuild scripts) and consumers
(serving): for every serving artifact it records the canonical SHA-256, size,
shape/row counts, the schema version it was validated against, and the inputs
and config knobs that produced the set.

Text artifacts are hashed canonically (CRLF normalised to LF) so the same
manifest verifies on Windows and Linux checkouts. Artifacts that are not
committed (window vectors, audio vectors) are marked optional: verification
warns about them instead of failing.

Usage:
    python scripts/build_artifact_manifest.py
    python scripts/verify_artifacts.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

if __package__ in {None, ""}:  # allow `python data_engineering/artifacts.py`
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_engineering.schemas import SCHEMAS  # noqa: E402

MANIFEST_FORMAT_VERSION = 1
MANIFEST_NAME = "projectr-serving"
DEFAULT_MANIFEST_PATH = "music_rec_artifacts/artifact_manifest.json"


@dataclass(frozen=True)
class Artifact:
    name: str
    path: str  # relative to the project root, forward slashes
    kind: str  # csv | json | npy | npz | faiss
    text: bool = False  # canonicalise CRLF -> LF before hashing
    schema: str | None = None
    required: bool = True


@dataclass(frozen=True)
class InputArtifact:
    name: str
    path: str
    text: bool = True
    required: bool = False


# Serving artifacts; optional entries may legitimately be absent from a
# checkout (they are large regenerable vectors kept out of git).
ARTIFACTS: tuple[Artifact, ...] = (
    Artifact("cleaned_lyrics", "music_rec_artifacts/cleaned_lyrics.csv", "csv",
             text=True, schema="cleaned_lyrics"),
    Artifact("embedding_ids", "music_rec_artifacts/embedding_ids.json", "json", text=True),
    Artifact("embeddings", "music_rec_artifacts/embeddings.npy", "npy"),
    Artifact("feature_meta", "music_rec_artifacts/feature_meta.json", "json", text=True),
    Artifact("feature_matrix", "music_rec_artifacts/feature_matrix.npy", "npy"),
    Artifact("lyrics_index", "music_rec_artifacts/lyrics.faiss", "faiss"),
    Artifact("mood_probe", "music_rec_artifacts/mood_probe.npz", "npz"),
    Artifact("mood_vectors", "music_rec_artifacts/mood_vectors.csv", "csv", text=True),
    Artifact("sentiment_scores", "music_rec_artifacts/sentiment_scores.csv", "csv",
             text=True, schema="sentiment_scores"),
    Artifact("window_vectors", "music_rec_artifacts/window_vectors.npy", "npy", required=False),
    Artifact("window_owners", "music_rec_artifacts/window_owners.npy", "npy", required=False),
    Artifact("audio_embeddings", "R_data/audio/audio_embeddings.npy", "npy", required=False),
    Artifact("audio_embedding_keys", "R_data/audio/audio_embedding_keys.csv", "csv", text=True),
    Artifact("audio_track_matches", "R_data/audio/audio_track_matches.csv", "csv",
             text=True, schema="audio_track_matches"),
)

# Provenance inputs: files the serving set was derived from.
INPUTS: tuple[InputArtifact, ...] = (
    InputArtifact("corpus_source", "CSVs Dataset/corpus_final_v3.csv"),
    InputArtifact("mood_labels", "R_data/raw/gemini/corpus_v3/labels_merged.csv"),
    InputArtifact("audio_new_songs", "R_data/audio/audio_new_songs_v2.csv"),
)

# Config knobs that change the content of the artifacts above.
CONFIG_KEYS = ("embedding_model", "embed_window_tokens", "embed_window_stride", "min_tokens")


def sha256_file(path: Path, *, text: bool = False) -> str:
    if text:
        return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _digest_ids(ids: list[str]) -> str:
    return _sha256_text(",".join(ids))


def _csv_metadata(path: Path, *, collect_ids: bool) -> tuple[int, str | None]:
    rows = 0
    ids: list[str] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None) or []
        id_index = header.index("song_id") if collect_ids and "song_id" in header else None
        for row in reader:
            if not row:
                continue
            rows += 1
            if id_index is not None and id_index < len(row):
                ids.append(row[id_index].strip())
    return rows, _digest_ids(ids) if id_index is not None else None


def describe(path: Path, artifact: Artifact, *, compute_hash: bool = True) -> dict:
    """Measure one artifact: hash, size and the metadata verify re-checks."""
    entry: dict = {
        "name": artifact.name,
        "path": artifact.path,
        "kind": artifact.kind,
        "text_normalized": artifact.text,
        "required": artifact.required,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path, text=artifact.text) if compute_hash else None,
        "schema": artifact.schema,
        "schema_version": SCHEMAS[artifact.schema].version if artifact.schema else None,
    }
    if artifact.kind == "csv":
        rows, id_digest = _csv_metadata(path, collect_ids=artifact.name == "cleaned_lyrics")
        entry["rows"] = rows
        if id_digest is not None:
            entry["id_digest"] = id_digest
    elif artifact.kind == "json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            entry["rows"] = len(payload)
            if all(isinstance(value, int) for value in payload):
                entry["id_digest"] = _digest_ids([str(value) for value in payload])
        elif isinstance(payload, dict):
            entry["keys"] = sorted(payload)
            entry["values"] = {
                key: value for key, value in payload.items()
                if isinstance(value, (int, float, str, bool))
            }
    elif artifact.kind == "npy":
        array = np.load(path, mmap_mode="r")
        entry["shape"] = [int(value) for value in array.shape]
        entry["dtype"] = str(array.dtype)
        if array.ndim >= 1:
            entry["rows"] = int(array.shape[0])
        if array.size and np.issubdtype(array.dtype, np.integer):
            entry["min"] = int(array.min())
            entry["max"] = int(array.max())
    elif artifact.kind == "npz":
        with np.load(path, allow_pickle=False) as archive:
            entry["arrays"] = {name: [int(value) for value in archive[name].shape]
                               for name in archive.files}
    elif artifact.kind == "faiss":
        try:
            import faiss  # type: ignore

            index = faiss.read_index(str(path))
            entry["ntotal"] = int(index.ntotal)
            entry["rows"] = int(index.ntotal)
            entry["dimension"] = int(index.d)
        except Exception as exc:  # ImportError in CI, RuntimeError when unreadable
            entry["note"] = f"faiss index not re-read: {exc}"
    else:
        raise ValueError(f"unknown artifact kind {artifact.kind!r} for {artifact.name}")
    return entry


def run_consistency_checks(entries: list[dict]) -> list[dict]:
    """Cross-artifact invariants; returns a list of {check, passed, detail}."""
    by_name = {entry["name"]: entry for entry in entries if not entry.get("missing")}
    results: list[dict] = []

    def record(check: str, passed: bool, detail: str) -> None:
        results.append({"check": check, "passed": passed, "detail": detail})

    def same_field(check: str, names: list[str], field: str) -> None:
        present = {name: by_name[name][field] for name in names
                   if name in by_name and field in by_name[name]}
        if len(present) < 2:
            record(check, True, f"skipped (measured: {', '.join(sorted(present)) or 'none'})")
            return
        distinct = {json.dumps(value, sort_keys=True) for value in present.values()}
        detail = "; ".join(f"{name}={value}" for name, value in present.items())
        record(check, len(distinct) == 1, detail)

    same_field(
        "song_rows_match",
        ["cleaned_lyrics", "embedding_ids", "embeddings", "sentiment_scores",
         "mood_vectors", "feature_matrix", "lyrics_index"],
        "rows",
    )
    same_field("corpus_embedding_id_order", ["cleaned_lyrics", "embedding_ids"], "id_digest")
    same_field("window_rows_match", ["window_vectors", "window_owners"], "rows")
    same_field("audio_rows_match",
               ["audio_embedding_keys", "audio_track_matches", "audio_embeddings"], "rows")

    owners = by_name.get("window_owners", {})
    song_rows = by_name.get("cleaned_lyrics", {}).get("rows")
    if owners.get("max") is not None and song_rows is not None:
        record("window_owner_range", owners["max"] < song_rows,
               f"max owner {owners['max']} < {song_rows} songs")
    else:
        record("window_owner_range", True, "skipped (window artifacts absent)")

    embeddings = by_name.get("embeddings", {}).get("shape")
    feature_matrix = by_name.get("feature_matrix", {}).get("shape")
    feature_meta = by_name.get("feature_meta", {}).get("values", {})
    problems: list[str] = []
    if embeddings and feature_meta.get("embedding_dim") is not None \
            and embeddings[1] != feature_meta["embedding_dim"]:
        problems.append(f"embeddings width {embeddings[1]} != feature_meta {feature_meta['embedding_dim']}")
    if feature_matrix and feature_meta.get("feature_dim") is not None \
            and feature_matrix[1] != feature_meta["feature_dim"]:
        problems.append(f"feature width {feature_matrix[1]} != feature_meta {feature_meta['feature_dim']}")
    if embeddings and feature_matrix and feature_matrix[1] < embeddings[1]:
        problems.append(f"feature width {feature_matrix[1]} < embedding width {embeddings[1]}")
    record("feature_layout_match", not problems, "; ".join(problems) or "ok")

    index = by_name.get("lyrics_index", {})
    if index.get("dimension") is not None and feature_matrix:
        record("index_dimension_match", index["dimension"] == feature_matrix[1],
               f"faiss dim {index['dimension']} vs feature width {feature_matrix[1]}")
    else:
        record("index_dimension_match", True, "skipped (faiss metadata or feature matrix absent)")

    probe_widths = {name: shape[1]
                    for name, shape in (by_name.get("mood_probe", {}).get("arrays") or {}).items()
                    if len(shape) == 2}
    if probe_widths and embeddings:
        record("probe_width_match", all(width == embeddings[1] for width in probe_widths.values()),
               f"probe widths {probe_widths} vs embedding width {embeddings[1]}")
    else:
        record("probe_width_match", True, "skipped (probe or embeddings absent)")
    return results


def config_snapshot(config) -> dict:
    if config is None:
        return {}
    return {key: getattr(config, key) for key in CONFIG_KEYS if hasattr(config, key)}


def git_revision(root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except OSError:  # pragma: no cover - git unavailable
        return None
    return completed.stdout.strip() if completed.returncode == 0 else None


def build_manifest(root: Path, artifacts: tuple[Artifact, ...] = ARTIFACTS,
                   inputs: tuple[InputArtifact, ...] = INPUTS, *, config=None) -> dict:
    missing = [artifact.name for artifact in artifacts
               if artifact.required and not (root / artifact.path).exists()]
    if missing:
        raise FileNotFoundError(f"required artifacts missing: {sorted(missing)}")

    entries: list[dict] = []
    for artifact in artifacts:
        path = root / artifact.path
        if path.exists():
            entries.append(describe(path, artifact))
        else:
            entries.append({"name": artifact.name, "path": artifact.path, "kind": artifact.kind,
                            "required": artifact.required, "missing": True})

    input_entries: list[dict] = []
    for source in inputs:
        path = root / source.path
        if path.exists():
            input_entries.append({"name": source.name, "path": source.path,
                                  "text_normalized": source.text,
                                  "bytes": path.stat().st_size,
                                  "sha256": sha256_file(path, text=source.text)})
        else:
            input_entries.append({"name": source.name, "path": source.path,
                                  "required": source.required, "missing": True})

    checks = run_consistency_checks(entries)
    failed = [check for check in checks if not check["passed"]]
    if failed:
        detail = "; ".join(f"{check['check']}: {check['detail']}" for check in failed)
        raise ValueError(f"artifact set is inconsistent: {detail}")

    snapshot = config_snapshot(config)
    return {
        "format_version": MANIFEST_FORMAT_VERSION,
        "name": MANIFEST_NAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": git_revision(root),
        "config": snapshot,
        "config_hash": _sha256_text(json.dumps(snapshot, sort_keys=True)),
        "inputs": input_entries,
        "artifacts": entries,
        "checks": checks,
    }


def verify_manifest(root: Path, manifest: dict, *, check_hashes: bool = True) -> dict:
    """Re-measure every artifact and input, then re-run cross-artifact checks."""
    errors: list[str] = []
    warnings: list[str] = []
    if manifest.get("format_version") != MANIFEST_FORMAT_VERSION:
        errors.append(f"manifest format_version {manifest.get('format_version')!r} "
                      f"!= {MANIFEST_FORMAT_VERSION}")

    current_entries: list[dict] = []
    for entry in manifest.get("artifacts", []):
        path = root / entry["path"]
        if entry.get("missing") or not path.exists():
            message = f"artifact {entry['name']} missing at {entry['path']}"
            (errors if entry.get("required", True) else warnings).append(message)
            continue
        artifact = Artifact(
            name=entry["name"], path=entry["path"], kind=entry["kind"],
            text=entry.get("text_normalized", False), schema=entry.get("schema"),
            required=entry.get("required", True),
        )
        try:
            current = describe(path, artifact, compute_hash=check_hashes)
        except Exception as exc:  # corrupted file must fail, not crash verification
            errors.append(f"artifact {entry['name']} unreadable: {exc}")
            continue
        current_entries.append(current)
        for key, expected in entry.items():
            if key == "note":
                continue
            if not check_hashes and key == "sha256":
                continue
            actual = current.get(key)
            if actual == expected:
                continue
            if key not in current and current.get("note"):
                warnings.append(f"{entry['name']}.{key} not re-measured: {current['note']}")
            else:
                errors.append(f"{entry['name']}.{key}: recorded {expected!r}, found {actual!r}")

    for entry in manifest.get("inputs", []):
        path = root / entry["path"]
        if not path.exists():
            warnings.append(f"input {entry['name']} missing at {entry['path']}")
            continue
        if not check_hashes:
            continue
        actual = sha256_file(path, text=entry.get("text_normalized", False))
        if actual != entry.get("sha256"):
            errors.append(f"input {entry['name']} content changed: "
                          f"sha256 {actual[:12]}... != {entry.get('sha256', '?')[:12]}...")

    checks = run_consistency_checks(current_entries)
    errors.extend(f"consistency {check['check']}: {check['detail']}"
                  for check in checks if not check["passed"])

    return {
        "passed": not errors,
        "manifest": manifest.get("name"),
        "generated_at": manifest.get("generated_at"),
        "git_sha": manifest.get("git_sha"),
        "artifacts_verified": len(current_entries),
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }


def format_manifest_summary(manifest: dict) -> str:
    lines = [f"manifest {manifest.get('name')} format v{manifest.get('format_version')} "
             f"git={manifest.get('git_sha')} generated={manifest.get('generated_at')}"]
    for entry in manifest.get("artifacts", []):
        if entry.get("missing"):
            lines.append(f"  - {entry['name']:<22} missing (optional)")
            continue
        metadata = ""
        if "rows" in entry:
            metadata += f" rows={entry['rows']}"
        if "shape" in entry:
            metadata += f" shape={tuple(entry['shape'])}"
        if entry.get("ntotal") is not None:
            metadata += f" ntotal={entry['ntotal']}"
        lines.append(f"  - {entry['name']:<22} {entry['kind']:<5} "
                     f"{entry['bytes'] / 1e6:9.2f} MB{metadata}")
    inputs = ", ".join(entry["name"] for entry in manifest.get("inputs", []))
    lines.append(f"  inputs: {inputs}")
    return "\n".join(lines)


def format_verify_report(report: dict) -> str:
    status = "PASS" if report["passed"] else "FAIL"
    lines = [f"[{status}] {report.get('manifest')} git={report.get('git_sha')} "
             f"artifacts_verified={report['artifacts_verified']}"]
    for check in report["checks"]:
        marker = "ok  " if check["passed"] else "FAIL"
        lines.append(f"    {marker} {check['check']}: {check['detail']}")
    for warning in report["warnings"]:
        lines.append(f"    warn {warning}")
    for error in report["errors"]:
        lines.append(f"    error {error}")
    return "\n".join(lines)
