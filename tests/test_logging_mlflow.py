"""Tests for MLflowLogger backend.

These tests exercise logging of params, metrics, and branches. They will be
skipped automatically if MLflow is not installed.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from spearmint.branch import Branch
from spearmint.logging import MLflowLogger

try:
    import mlflow  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover - MLflow not available
    mlflow = None

pytestmark = pytest.mark.skipif(mlflow is None, reason="MLflow not installed")


def _make_branch(config_id: str, status: str = "success") -> Branch:
    b = Branch.start(config_id=config_id, config={"delta": 1})
    if status == "success":
        b.mark_success(output=42)
    elif status == "failed":
        b.mark_failure(RuntimeError("boom"))
    else:
        b.mark_skipped("n/a")
    return b


@pytest.fixture()
def tracking_dir(tmp_path: Path) -> Generator[str, None, None]:
    # Use a temporary tracking URI to isolate test runs
    tracking_uri = tmp_path / "mlruns"
    yield f"file:{tracking_uri}"


def test_start_and_end_run(tracking_dir: str) -> None:
    logger = MLflowLogger(tracking_uri=tracking_dir, experiment_name="test-exp")
    logger.start_run("runA")
    underlying_id = logger.get_mlflow_run_id("runA")
    assert underlying_id is not None
    logger.end_run("runA")


def test_log_params_and_metrics(tracking_dir: str) -> None:
    logger = MLflowLogger(tracking_uri=tracking_dir, experiment_name="test-exp")
    run_id = "runB"
    logger.start_run(run_id)
    logger.log_params(run_id, {"model": "gpt", "lr": 0.01})
    logger.log_metrics(run_id, {"accuracy": 0.9, "loss": 0.1})

    mlflow_run_id = logger.get_mlflow_run_id(run_id)
    assert mlflow_run_id is not None
    run_data = mlflow.get_run(mlflow_run_id)
    assert run_data.data.params["model"] == "gpt"
    assert run_data.data.params["lr"] == "0.01"  # MLflow stores params as strings
    assert run_data.data.metrics["accuracy"] == 0.9
    assert run_data.data.metrics["loss"] == 0.1


def test_log_branch_artifact(tracking_dir: str) -> None:
    logger = MLflowLogger(tracking_uri=tracking_dir, experiment_name="test-exp")
    run_id = "runC"
    logger.start_run(run_id)
    branch = _make_branch("cfg1")
    logger.log_branch(run_id, branch)

    mlflow_run_id = logger.get_mlflow_run_id(run_id)
    assert mlflow_run_id is not None

    # Fetch run info and inspect artifacts directory.
    client = mlflow.tracking.MlflowClient()
    artifacts = client.list_artifacts(mlflow_run_id)
    artifact_names = {a.path for a in artifacts}
    # Expect exactly one artifact file for the branch JSON
    assert any(name.startswith("branch_cfg1") and name.endswith(".json") for name in artifact_names)
