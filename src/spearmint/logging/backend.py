"""Logging backend protocol definitions.

This module defines the `LoggerBackend` protocol used by all logging backends.
Separated from concrete implementations to keep dependencies minimal.

TODO:
- Drop logger implementation
- Replace with tracing instead
    (e.g., OpenTelemetry) for more flexible logging?
    https://mlflow.org/docs/latest/genai/tracing/track-environments-context/#programmatic-analysis
"""

from __future__ import annotations

from typing import Any, Protocol

from ..branch import Branch


class LoggerBackend(Protocol):
    """Protocol defining the interface for experiment logging backends."""

    def start_run(self, run_id: str) -> None:  # pragma: no cover - interface
        """Start a new experiment run.

        Args:
            run_id: Unique identifier for this run
        """
        ...

    def end_run(self, run_id: str) -> None:  # pragma: no cover - interface
        """End an experiment run.

        Args:
            run_id: Unique identifier for the run to end
        """
        ...

    def log_params(
        self, run_id: str, params: dict[str, Any]
    ) -> None:  # pragma: no cover - interface
        """Log parameters for a run.

        Args:
            run_id: Unique identifier for the run
            params: Dictionary of parameter names and values to log
        """
        ...

    def log_metrics(
        self, run_id: str, metrics: dict[str, float]
    ) -> None:  # pragma: no cover - interface
        """Log metrics for a run.

        Args:
            run_id: Unique identifier for the run
            metrics: Dictionary of metric names and values to log
        """
        ...

    def log_branch(self, run_id: str, branch: Branch) -> None:  # pragma: no cover - interface
        """Log a completed branch execution.

        Args:
            run_id: Unique identifier for the run
            branch: Branch instance with execution results
        """
        ...


__all__ = ["LoggerBackend"]
