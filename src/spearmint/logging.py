"""Logging backend abstraction and implementations.

This module provides a pluggable logging interface for experiment tracking,
with support for MLflow and in-memory test backends.

Acceptance Criteria Reference: Section 2.4 (Logging Layer)
- LoggerBackend protocol defining logging interface
- MLflow backend implementation with graceful fallback
- InMemoryLogger for testing
"""

from typing import Any, Optional, Protocol

from .branch import Branch


class LoggerBackend(Protocol):
    """Protocol defining the interface for experiment logging backends."""

    def start_run(self, run_id: str) -> None:
        """Start a new experiment run.

        Args:
            run_id: Unique identifier for this run
        """
        ...

    def end_run(self, run_id: str) -> None:
        """End an experiment run.

        Args:
            run_id: Unique identifier for the run to end
        """
        ...

    def log_params(self, run_id: str, params: dict[str, Any]) -> None:
        """Log parameters for a run.

        Args:
            run_id: Unique identifier for the run
            params: Dictionary of parameter names and values to log
        """
        ...

    def log_metrics(self, run_id: str, metrics: dict[str, float]) -> None:
        """Log metrics for a run.

        Args:
            run_id: Unique identifier for the run
            metrics: Dictionary of metric names and values to log
        """
        ...

    def log_branch(self, run_id: str, branch: Branch) -> None:
        """Log a completed branch execution.

        Args:
            run_id: Unique identifier for the run
            branch: Branch instance with execution results
        """
        ...


class InMemoryLogger:
    """In-memory logger backend for testing purposes.

    Stores all logged data in memory for inspection during tests.
    """

    def __init__(self) -> None:
        """Initialize the in-memory logger."""
        self.runs: dict[str, dict[str, Any]] = {}
        self.params: dict[str, dict[str, Any]] = {}
        self.metrics: dict[str, dict[str, float]] = {}
        self.branches: dict[str, list[Branch]] = {}

    def start_run(self, run_id: str) -> None:
        """Start a new experiment run."""
        self.runs[run_id] = {"started": True, "ended": False}
        self.params[run_id] = {}
        self.metrics[run_id] = {}
        self.branches[run_id] = []

    def end_run(self, run_id: str) -> None:
        """End an experiment run."""
        if run_id in self.runs:
            self.runs[run_id]["ended"] = True

    def log_params(self, run_id: str, params: dict[str, Any]) -> None:
        """Log parameters for a run."""
        if run_id not in self.params:
            self.params[run_id] = {}
        self.params[run_id].update(params)

    def log_metrics(self, run_id: str, metrics: dict[str, float]) -> None:
        """Log metrics for a run."""
        if run_id not in self.metrics:
            self.metrics[run_id] = {}
        self.metrics[run_id].update(metrics)

    def log_branch(self, run_id: str, branch: Branch) -> None:
        """Log a completed branch execution."""
        if run_id not in self.branches:
            self.branches[run_id] = []
        self.branches[run_id].append(branch)

    def get_run_count(self) -> int:
        """Get the total number of runs started."""
        return len(self.runs)

    def get_branch_count(self, run_id: Optional[str] = None) -> int:
        """Get the total number of branches logged.

        Args:
            run_id: If provided, count branches for specific run only

        Returns:
            Number of branches logged
        """
        if run_id is not None:
            return len(self.branches.get(run_id, []))
        return sum(len(branches) for branches in self.branches.values())


__all__ = ["LoggerBackend", "InMemoryLogger"]
