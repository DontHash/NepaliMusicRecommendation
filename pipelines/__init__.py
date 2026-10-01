"""ProjectR pipelines: a thin, declarative asset graph runner.

See docs/DE3_ORCHESTRATION_PLAN.md for the design and asset catalog. The runner
is intentionally small (execution, resume, history) so a full orchestrator
(Dagster/Prefect) can wrap the same asset definitions later.
"""

from pipelines.core import PROJECT_ROOT, Asset, RunContext, script_action
from pipelines.runner import Pipeline

__all__ = ["PROJECT_ROOT", "Asset", "RunContext", "script_action", "Pipeline"]
