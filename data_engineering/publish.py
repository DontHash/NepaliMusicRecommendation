"""Versioned artifact publishing: snapshot, verify, atomic pointer swap.

Publishing turns the staging artifact set (what the rebuild scripts write) into
an immutable version directory plus a ``current.json`` pointer:

    music_rec_artifacts/
      versions/<version-id>/
        music_rec_artifacts/...     <- mirrored serving artifacts
        R_data/audio/...            <- mirrored audio artifacts
        manifest.json               <- recorded hashes, metadata, provenance
      current.json                  <- pointer read by serving (atomic swap)

The copy is verified against its own manifest before the directory is renamed
into place, and the pointer swap is a single atomic replace, so a reader either
sees the old version or the new one, never a half-written set. Rollback is just
another pointer swap; old versions are retained up to ``keep``.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_engineering.artifacts import (  # noqa: E402
    ARTIFACTS,
    INPUTS,
    build_manifest,
    git_revision,
    sha256_file,
    verify_manifest,
)

VERSIONS_DIRNAME = "versions"
POINTER_FILENAME = "current.json"
DEFAULT_KEEP = 3


def default_pointer_path(root: Path) -> Path:
    return root / "music_rec_artifacts" / POINTER_FILENAME


def version_dir_for(pointer_path: Path, version: str) -> Path:
    return pointer_path.parent / VERSIONS_DIRNAME / version


def read_pointer(pointer_path: Path) -> dict | None:
    try:
        return json.loads(pointer_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_pointer(pointer_path: Path, pointer: dict) -> None:
    """Atomic pointer swap: write a temp file, then replace."""
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    temp = pointer_path.parent / (pointer_path.name + ".tmp")
    temp.write_text(json.dumps(pointer, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(pointer_path)


def list_versions(pointer_path: Path) -> list[dict]:
    """Newest first; only directories carrying a manifest count as versions."""
    versions_dir = pointer_path.parent / VERSIONS_DIRNAME
    current = (read_pointer(pointer_path) or {}).get("version")
    items: list[dict] = []
    if not versions_dir.is_dir():
        return items
    for path in sorted(versions_dir.iterdir(), reverse=True):
        manifest_path = path / "manifest.json"
        if not path.is_dir() or not manifest_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        items.append({
            "version": path.name,
            "path": str(path),
            "published_at": manifest.get("published_at"),
            "git_sha": manifest.get("git_sha"),
            "artifacts": sum(1 for entry in manifest.get("artifacts", [])
                             if not entry.get("missing")),
            "current": path.name == current,
        })
    return items


def _new_version_id(root: Path) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    revision = git_revision(root) or "nogit"
    return f"{stamp}-{revision[:7]}"


def publish_artifacts(root: Path, pointer_path: Path | None = None, *,
                      artifacts=ARTIFACTS, inputs=INPUTS, version: str | None = None,
                      keep: int = DEFAULT_KEEP, dry_run: bool = False,
                      config=None) -> dict:
    """Snapshot the staging set into a version directory and point at it."""
    pointer_path = pointer_path or default_pointer_path(root)
    staging_manifest = build_manifest(root, artifacts, inputs, config=config)
    version = version or _new_version_id(root)
    destination = version_dir_for(pointer_path, version)
    if destination.exists():
        raise FileExistsError(f"version {version} already exists at {destination}")

    copied: list[str] = []
    missing_optional: list[str] = []
    total_bytes = 0
    pruned: list[str] = []
    published_manifest: dict | None = None

    if not dry_run:
        staging = destination.parent / (destination.name + ".tmp")
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        try:
            for entry in staging_manifest["artifacts"]:
                if entry.get("missing"):
                    missing_optional.append(entry["name"])
                    continue
                source = root / entry["path"]
                target = staging / entry["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                copied.append(entry["name"])
                total_bytes += entry["bytes"]

            published_manifest = dict(staging_manifest)
            published_manifest["version"] = version
            published_manifest["published_at"] = datetime.now(timezone.utc).isoformat()
            (staging / "manifest.json").write_text(
                json.dumps(published_manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            # Verify the copy before it becomes visible; inputs are provenance
            # only and are not copied into the version directory.
            report = verify_manifest(staging, {**published_manifest, "inputs": []})
            if not report["passed"]:
                raise ValueError("published copy failed verification: "
                                 + "; ".join(report["errors"]))

            staging.rename(destination)
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise

        pointer = {
            "version": version,
            "published_at": published_manifest["published_at"],
            "manifest": f"{VERSIONS_DIRNAME}/{version}/manifest.json",
            "manifest_sha256": sha256_file(destination / "manifest.json", text=True),
            "artifacts": len(copied),
            "copy_bytes": total_bytes,
        }
        write_pointer(pointer_path, pointer)
        pruned = prune_versions(pointer_path, keep=keep)
    else:
        pointer = {"version": version, "dry_run": True}

    return {
        "version": version,
        "pointer": str(pointer_path),
        "destination": str(destination),
        "copied": copied,
        "missing_optional": missing_optional,
        "bytes": total_bytes,
        "pruned": pruned,
        "pointer_doc": pointer,
        "dry_run": dry_run,
        "staging_manifest": staging_manifest,
    }


def prune_versions(pointer_path: Path, *, keep: int = DEFAULT_KEEP,
                   dry_run: bool = False) -> list[str]:
    """Delete old version directories, never the pointer's current version."""
    if keep < 1:
        raise ValueError("keep must be >= 1")
    versions = list_versions(pointer_path)
    if len(versions) <= keep:
        return []
    current = {item["version"] for item in versions if item["current"]}
    keep_set = {item["version"] for item in versions[:keep]} | current
    pruned: list[str] = []
    for item in versions:
        if item["version"] in keep_set:
            continue
        if not dry_run:
            shutil.rmtree(item["path"], ignore_errors=True)
        pruned.append(item["version"])
    return pruned
