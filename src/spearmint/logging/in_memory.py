"""In-memory logger backend implementation."""

from __future__ import annotations

from typing import Any

from ..branch import Branch
from .backend import LoggerBackend


class InMemoryLogger(LoggerBackend):
    """In-memory logger backend for testing purposes.

    Stores all logged data in memory for inspection during tests.
    """

    def __init__(self) -> None:
        self.runs: dict[str, dict[str, Any]] = {}
        self.params: dict[str, dict[str, Any]] = {}
        self.metrics: dict[str, dict[str, float]] = {}
        self.branches: dict[str, list[Branch]] = {}

    def start_run(self, run_id: str) -> None:
        self.runs[run_id] = {"started": True, "ended": False}
        self.params[run_id] = {}
        self.metrics[run_id] = {}
        self.branches[run_id] = []

    def end_run(self, run_id: str) -> None:
        if run_id in self.runs:
            self.runs[run_id]["ended"] = True

    def log_params(self, run_id: str, params: dict[str, Any]) -> None:
        if run_id not in self.params:
            self.params[run_id] = {}
        self.params[run_id].update(params)

    def log_metrics(self, run_id: str, metrics: dict[str, float]) -> None:
        if run_id not in self.metrics:
            self.metrics[run_id] = {}
        self.metrics[run_id].update(metrics)

    def log_branch(self, run_id: str, branch: Branch) -> None:
        if run_id not in self.branches:
            self.branches[run_id] = []
        self.branches[run_id].append(branch)

    def get_run_count(self) -> int:
        return len(self.runs)

    def get_branch_count(self, run_id: str | None = None) -> int:
        if run_id is not None:
            return len(self.branches.get(run_id, []))
        return sum(len(branches) for branches in self.branches.values())


__all__ = ["InMemoryLogger"]
