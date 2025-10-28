"""Branch data structures for experiment execution tracking.

This module provides core data models for tracking individual experiment branches,
including configuration, timing, status, and results.

Acceptance Criteria Reference: Section 2.2 (Branch Model)
- Branch dataclass with config_id, config, timestamps, status, output, exception info
- Factory methods for lifecycle management (start, mark_success, mark_failure)
- BranchContainer for managing collections of branches

TODO:
- Add redaction logic for sensitive config data
- Extended metrics (retry counts, etc.)
- Config object type normalization (Pydantic model vs dict)
"""

import time
import traceback as tb
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from .types import ExceptionInfo, Status

TModel = TypeVar("TModel", bound=BaseModel)


@dataclass
class Branch(Generic[TModel]):
    """Represents a single execution branch of an experiment.

    A Branch tracks the configuration, execution timing, status, output,
    and any exceptions that occur during the execution of an experiment variant.
    """

    config_id: str
    config: Sequence[TModel]
    start_ts: float
    end_ts: float | None = None
    status: Status = "pending"
    output: Any = None
    exception_info: ExceptionInfo | None = None

    @classmethod
    def start(cls, config_id: str, config: Sequence[TModel]) -> "Branch[TModel]":
        """Create a new Branch with initialized start timestamp.

        Args:
            config_id: Unique identifier for this configuration
            config: Configuration dictionary for this branch

        Returns:
            New Branch instance with start_ts set to current time
        """
        return cls(
            config_id=config_id,
            config=config,
            start_ts=time.perf_counter(),
        )

    @property
    def duration(self) -> float | None:
        """Calculate execution duration in seconds.

        Returns:
            Duration in seconds if branch is completed, None otherwise
        """
        if self.end_ts is None:
            return None
        return self.end_ts - self.start_ts

    def mark_success(self, output: Any) -> None:
        """Mark branch as successfully completed.

        Args:
            output: The result/output of the branch execution

        Raises:
            RuntimeError: If branch already finalized
        """
        self._finalize(status="success", output=output)

    def mark_failure(self, exc: Exception) -> None:
        """Mark branch as failed and capture exception details.

        Args:
            exc: The exception that caused the failure

        Raises:
            RuntimeError: If branch already finalized
        """
        exc_info: ExceptionInfo = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": "".join(tb.format_exception(type(exc), exc, exc.__traceback__)),
        }
        self._finalize(status="failed", exception_info=exc_info)

    def mark_skipped(self, reason: str) -> None:
        """Mark branch as skipped with a reason.

        Args:
            reason: Explanation for why branch was skipped

        Raises:
            RuntimeError: If branch already finalized
        """
        exc_info: ExceptionInfo = {
            "type": "Skipped",
            "message": reason,
            "traceback": "",
        }
        self._finalize(status="skipped", exception_info=exc_info)

    def _finalize(
        self,
        status: Status,
        output: Any = None,
        exception_info: ExceptionInfo | None = None,
    ) -> None:
        """Internal method to finalize branch state.

        Args:
            status: Final status of the branch
            output: Optional output data
            exception_info: Optional exception information

        Raises:
            RuntimeError: If branch already finalized
        """
        if self.status != "pending":
            raise RuntimeError(
                f"Branch already finalized with status '{self.status}'. "
                "Cannot change status after finalization."
            )

        self.end_ts = time.perf_counter()
        self.status = status
        if output is not None:
            self.output = output
        if exception_info is not None:
            self.exception_info = exception_info

    def to_dict(self, redact: bool = False) -> dict[str, Any]:
        """Convert branch to dictionary representation.

        Args:
            redact: If True, redact sensitive information (TODO: implement)

        Returns:
            Dictionary with all branch fields
        """
        # TODO: Implement redaction logic for sensitive config data
        return {
            "config_id": self.config_id,
            "config": self.config,
            "start_ts": self.start_ts,
            "end_ts": self.end_ts,
            "status": self.status,
            "output": self.output,
            "exception_info": self.exception_info,
            "duration": self.duration,
        }


class BranchContainer(Generic[TModel]):
    """Container for managing collections of Branch instances.

    Provides iteration, indexing, and filtering capabilities for branch collections.
    """

    def __init__(self, branches: list[Branch[TModel]]) -> None:
        """Initialize container with list of branches.

        Args:
            branches: List of Branch instances to manage
        """
        self.branches = branches

    def __iter__(self) -> Iterator[Branch[TModel]]:
        """Allow iteration over branches."""
        return iter(self.branches)

    def __len__(self) -> int:
        """Return number of branches in container."""
        return len(self.branches)

    def __getitem__(self, index: int) -> Branch[TModel]:
        """Allow indexing into branch collection.

        Args:
            index: Index of branch to retrieve

        Returns:
            Branch at specified index
        """
        return self.branches[index]

    def successful(self) -> list[Branch[TModel]]:
        """Filter and return only successful branches.

        Returns:
            List of branches with status 'success'
        """
        return [b for b in self.branches if b.status == "success"]

    def failed(self) -> list[Branch[TModel]]:
        """Filter and return only failed branches.

        Returns:
            List of branches with status 'failed'
        """
        return [b for b in self.branches if b.status == "failed"]

    def by_config_id(self, config_id: str) -> Branch[TModel] | None:
        """Find branch by configuration ID.

        Args:
            config_id: Configuration ID to search for

        Returns:
            Branch with matching config_id, or None if not found
        """
        for branch in self.branches:
            if branch.config_id == config_id:
                return branch
        return None

    def add(self, branch: Branch[TModel]) -> None:
        """Add a branch to the container.

        Args:
            branch: Branch instance to add
        """
        self.branches.append(branch)


__all__ = ["Branch", "BranchContainer", "TModel"]
