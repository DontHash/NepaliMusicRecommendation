"""Dependency-aware execution for the ProjectR asset graph."""

from __future__ import annotations

import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from pipelines.core import PROJECT_ROOT, Asset, RunContext
from pipelines.metrics import MetricsWriter
from pipelines.state import RunStore, utcnow

STATUS_OK = "ok"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"
STATUS_BLOCKED = "blocked"
STATUS_EXTERNAL = "external"

TERMINAL_FAILURES = {STATUS_FAILED, STATUS_BLOCKED}


class _Tee:
    def __init__(self, original, handle):
        self.original = original
        self.handle = handle

    def write(self, data: str) -> int:
        self.original.write(data)
        self.handle.write(data)
        return len(data)

    def flush(self) -> None:
        self.original.flush()
        self.handle.flush()


class Pipeline:
    def __init__(self, assets: Sequence[Asset], *, project_root: Path = PROJECT_ROOT,
                 state_dir: Path | None = None, config=None):
        self.project_root = Path(project_root)
        self.state_dir = Path(state_dir) if state_dir else self.project_root / "R_data" / "state"
        self.config = config
        self.assets = list(assets)
        self.assets_by_name: dict[str, Asset] = {}
        for asset in self.assets:
            if asset.name in self.assets_by_name:
                raise ValueError(f"duplicate asset {asset.name!r}")
            self.assets_by_name[asset.name] = asset
        for asset in self.assets:
            for dependency in asset.deps:
                if dependency not in self.assets_by_name:
                    raise ValueError(
                        f"asset {asset.name!r} depends on unknown asset {dependency!r}")
        self.order = self._topological_order()
        self.state = RunStore(self.state_dir / "runs.sqlite")
        self.metrics = MetricsWriter(self.state_dir / "metrics.jsonl")

    # -- graph ---------------------------------------------------------------
    def _topological_order(self) -> list[str]:
        order: list[str] = []
        visiting: set[str] = set()
        done: set[str] = set()

        def visit(name: str) -> None:
            if name in done:
                return
            if name in visiting:
                raise ValueError(f"dependency cycle detected at {name!r}")
            visiting.add(name)
            for dependency in self.assets_by_name[name].deps:
                visit(dependency)
            visiting.discard(name)
            done.add(name)
            order.append(name)

        for name in self.assets_by_name:
            visit(name)
        return order

    def graph(self) -> list[dict]:
        return [
            {"asset": asset.name, "deps": list(asset.deps), "outputs": list(asset.outputs),
             "external": asset.external, "description": asset.description}
            for asset in self.assets
        ]

    def descendants(self, names: Iterable[str]) -> set[str]:
        found: set[str] = set(names)
        queue = list(found)
        while queue:
            current = queue.pop()
            for asset in self.assets:
                if current in asset.deps and asset.name not in found:
                    found.add(asset.name)
                    queue.append(asset.name)
        return found

    # -- state ---------------------------------------------------------------
    def is_materialized(self, asset: Asset) -> bool:
        """Outputs are the state; history is the fallback for output-less assets."""
        if asset.outputs:
            return all((self.project_root / output).exists() for output in asset.outputs)
        return self.state.last_status(asset.name) == STATUS_OK

    def resolve(self, select: Sequence[str] | None, *, downstream: bool = False,
                backfill: bool = False) -> tuple[list[str], set[str]]:
        if select:
            unknown = [name for name in select if name not in self.assets_by_name]
            if unknown:
                raise KeyError(f"unknown asset(s): {', '.join(sorted(unknown))}")
            targets = set(select)
        else:
            targets = set(self.assets_by_name)
        if downstream or backfill:
            targets |= self.descendants(targets)

        needed = set(targets)
        changed = True
        while changed:  # pull in ancestors only when their outputs are missing
            changed = False
            for name in list(needed):
                for dependency in self.assets_by_name[name].deps:
                    if dependency in needed:
                        continue
                    if not self.is_materialized(self.assets_by_name[dependency]):
                        needed.add(dependency)
                        changed = True
        forced = set(targets) if backfill else set()
        return [name for name in self.order if name in needed], forced

    # -- execution -----------------------------------------------------------
    def run(self, *, select: Sequence[str] | None = None, downstream: bool = False,
            backfill: bool = False, force: bool = False, dry_run: bool = False,
            retries: int | None = None) -> dict:
        scope, forced = self.resolve(select, downstream=downstream, backfill=backfill)
        if force:
            forced = set(scope)

        if dry_run:
            plan = []
            for name in scope:
                asset = self.assets_by_name[name]
                if asset.external:
                    status = STATUS_EXTERNAL
                elif name in forced or not self.is_materialized(asset):
                    status = "run"
                else:
                    status = "skip"
                plan.append({"asset": name, "status": status})
            return {"dry_run": True, "run_id": None, "status": "dry-run", "plan": plan}

        options = {"select": list(select or []), "downstream": downstream,
                   "backfill": backfill, "force": force}
        run_id = self.state.start_run(targets=scope, options=options,
                                      git_sha=_git_sha(self.project_root))
        statuses: dict[str, str] = {}
        records: list[dict] = []
        run_started = time.perf_counter()

        for name in scope:
            asset = self.assets_by_name[name]
            started_at = utcnow()
            start = time.perf_counter()
            if asset.external:
                status, message, metadata = STATUS_EXTERNAL, "external source", {}
            elif any(statuses.get(dependency) in TERMINAL_FAILURES
                     for dependency in asset.deps):
                status, message, metadata = STATUS_BLOCKED, "dependency failed", {}
            elif name not in forced and self.is_materialized(asset):
                status, message, metadata = STATUS_SKIPPED, "outputs already present", {}
            else:
                status, message, metadata = self._execute(asset, run_id, retries)
            duration = round(time.perf_counter() - start, 3)
            self.state.record_asset(run_id, asset=name, status=status, started_at=started_at,
                                    finished_at=utcnow(), duration_s=duration,
                                    message=message, metadata=metadata)
            statuses[name] = status
            records.append({"asset": name, "status": status, "duration_s": duration,
                            "message": message, "metadata": metadata})
            self.metrics.emit("asset", run_id=run_id, asset=name, status=status,
                              duration_s=duration, message=message)

        run_status = (STATUS_FAILED if any(status in TERMINAL_FAILURES
                                           for status in statuses.values()) else STATUS_OK)
        run_duration = round(time.perf_counter() - run_started, 3)
        self.state.finish_run(run_id, run_status)
        self.metrics.emit("run", run_id=run_id, status=run_status,
                          assets=len(records), duration_s=run_duration,
                          select=list(select or []))
        return {"dry_run": False, "run_id": run_id, "status": run_status,
                "assets": records, "duration_s": run_duration}

    def _execute(self, asset: Asset, run_id: int,
                 retries: int | None) -> tuple[str, str, dict]:
        attempts = (asset.retries if retries is None else retries) + 1
        context = RunContext(project_root=self.project_root, state_dir=self.state_dir,
                             run_id=run_id, config=self.config)
        last_error = ""
        for attempt in range(1, attempts + 1):
            try:
                with self._capture_log(run_id, asset.name):
                    metadata = dict(asset.action(context) or {})  # type: ignore[misc]
                metadata["attempts"] = attempt
                return STATUS_OK, "", metadata
            except Exception as error:  # noqa: BLE001 - recorded as asset failure
                last_error = f"{type(error).__name__}: {error}"
                if attempt < attempts:
                    time.sleep(min(0.5 * attempt, 2.0))
        return STATUS_FAILED, last_error, {"attempts": attempts}

    @contextmanager
    def _capture_log(self, run_id: int, asset_name: str) -> Iterator[None]:
        log_path = (self.state_dir / "logs" / str(run_id)
                    / (asset_name.replace(".", "_") + ".log"))
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8") as handle:
            original_out, original_err = sys.stdout, sys.stderr
            sys.stdout = _Tee(original_out, handle)
            sys.stderr = _Tee(original_err, handle)
            try:
                yield
            finally:
                sys.stdout, sys.stderr = original_out, original_err


def _git_sha(project_root: Path) -> str | None:
    from data_engineering.artifacts import git_revision

    return git_revision(project_root)
