"""MLflow logger backend implementation.

Provides an implementation of `LoggerBackend` that logs experiment data to
MLflow. This backend is optional and requires the `mlflow` extra to be
installed:

    pip install spearmint-framework[mlflow]

Design notes:
- We map the user-provided `run_id` to the MLflow internal run id and store
  a mapping for later lookups.
- Branches are logged as JSON artifacts containing all branch fields and
  duration for easy offline analysis.
- If MLflow is not installed, an ImportError is raised upon construction.
- A lightweight convenience method `get_mlflow_run_id` is provided for tests
  or advanced introspection.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from ..branch import Branch
from .backend import LoggerBackend

try:  # pragma: no cover - import guard
    import mlflow  # type: ignore  # runtime import; stubs may be missing

    _IMPORT_ERROR: Exception | None = None
except Exception as e:  # pragma: no cover - we want clear error message
    mlflow = None
    _IMPORT_ERROR = e


class MLflowLogger(LoggerBackend):
    """MLflow-based experiment logger.

    Args:
        tracking_uri: Optional MLflow tracking URI. If provided, will be set
            via ``mlflow.set_tracking_uri`` during initialization.
        experiment_name: Optional MLflow experiment name. If provided, will
            be created or reused. If omitted, MLflow default experiment is used.

    Raises:
        ImportError: If MLflow is not installed.
    """

    def __init__(
        self,
        tracking_uri: str | None = None,
        experiment_name: str | None = None,
    ) -> None:
        if mlflow is None:  # pragma: no cover - safety path
            raise ImportError(
                "MLflow is not installed. Install with 'pip install spearmint-framework[mlflow]'"
            ) from _IMPORT_ERROR

        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        if experiment_name:
            mlflow.set_experiment(experiment_name)

        self._run_map: dict[str, str] = {}  # user run_id -> mlflow run id

    # Interface implementation -------------------------------------------------
    def start_run(self, run_id: str) -> None:
        """Start a new MLflow run (ends any active run first)."""
        assert mlflow is not None  # for type checkers
        active = mlflow.active_run()
        if active is not None:
            # End any lingering run to avoid nested complexity unless desired.
            # Occasionally the tracking URI may have changed causing the underlying run to be missing.
            # In that case we ignore the exception and proceed.
            try:  # pragma: no cover - defensive
                mlflow.end_run()
            except Exception:  # broad catch: mlflow exceptions hierarchy varies
                pass
        run = mlflow.start_run(run_name=run_id)
        self._run_map[run_id] = run.info.run_id

    def end_run(self, run_id: str) -> None:
        """End MLflow run if it's the one associated with run_id."""
        assert mlflow is not None
        active = mlflow.active_run()
        if active and run_id in self._run_map and active.info.run_id == self._run_map[run_id]:
            mlflow.end_run()

    def log_params(self, run_id: str, params: dict[str, Any]) -> None:
        assert mlflow is not None
        self._ensure_run(run_id)
        mlflow.log_params(params)

    def log_metrics(self, run_id: str, metrics: dict[str, float]) -> None:
        assert mlflow is not None
        self._ensure_run(run_id)
        mlflow.log_metrics(metrics)

    def log_branch(self, run_id: str, branch: Branch) -> None:
        assert mlflow is not None
        self._ensure_run(run_id)
        # Log key branch metadata as params for quick filtering
        branch_prefix = f"branch_{branch.config_id}"
        branch_params = {
            f"{branch_prefix}_status": branch.status,
            f"{branch_prefix}_duration": branch.duration,
        }
        mlflow.log_params(branch_params)
        # Store detailed branch info as an artifact JSON
        artifact_content = branch.to_dict()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / f"{branch_prefix}.json"
            artifact_path.write_text(json.dumps(artifact_content, indent=2))
            mlflow.log_artifact(str(artifact_path))

    # Helpers ------------------------------------------------------------------
    def _ensure_run(self, run_id: str) -> None:
        if run_id not in self._run_map:
            # Auto-start run if not started explicitly
            self.start_run(run_id)

    def get_mlflow_run_id(self, run_id: str) -> str | None:
        """Retrieve the underlying MLflow run id for a user-provided run id."""
        return self._run_map.get(run_id)


__all__ = ["MLflowLogger"]
