"""Asset primitives for the ProjectR pipeline runner."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ActionResult = Mapping[str, Any] | None


@dataclass(frozen=True)
class Asset:
    """One materializable step of the data graph."""

    name: str
    action: Callable[["RunContext"], ActionResult] | None = None
    deps: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    description: str = ""
    retries: int = 0
    external: bool = False

    def __post_init__(self) -> None:
        if self.external and self.action is not None:
            raise ValueError(f"external asset {self.name!r} must not define an action")
        if not self.external and self.action is None:
            raise ValueError(f"asset {self.name!r} needs an action or external=True")


@dataclass
class RunContext:
    project_root: Path
    state_dir: Path
    run_id: int
    config: Any = None

    def path(self, relative: str) -> Path:
        return self.project_root / relative


def script_action(script: str, *args: str) -> Callable[[RunContext], ActionResult]:
    """Run a repository script as a subprocess, relaying output into the asset log."""

    def action(context: RunContext) -> ActionResult:
        command = [sys.executable, str(context.project_root / script), *args]
        environment = dict(os.environ)
        environment.setdefault("PYTHONPATH", str(context.project_root))
        process = subprocess.Popen(
            command,
            cwd=str(context.project_root),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        tail: list[str] = []
        for line in process.stdout:  # type: ignore[union-attr]
            print(line.rstrip())
            tail.append(line.rstrip())
            if len(tail) > 20:
                tail.pop(0)
        code = process.wait()
        if code != 0:
            raise RuntimeError(f"{script} exited with {code}: " + " | ".join(tail[-5:]))
        return {"command": " ".join([script, *args])}

    return action
