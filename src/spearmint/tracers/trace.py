"""Tracing infrastructure for Spearmint framework.

Provides pluggable tracing backends via the abstract Tracer class.
Supports multiple simultaneous tracers using a contextvar-based stack.
"""

from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
from enum import Enum
from typing import Any


class TraceEvent(Enum):
    EXPERIMENT = "experiment"
    BRANCH = "branch"


class Tracer(ABC):
    """Abstract base class for Spearmint tracers."""

    @abstractmethod
    @contextmanager
    def trace(self, event: TraceEvent, context: dict[str, Any]) -> Generator[Any, None, None]:
        """Context manager for tracing a specific event.

        Args:
            event: TraceEvent enum value indicating the type of event
            context: Dictionary of contextual information for the trace
        Yields:
            Control to the traced code block
        """
        ...

    @abstractmethod
    def get_traces(self) -> Generator[dict[str, Any], None, None]:
        """Retrieve all recorded traces."""
        ...


class NoOpTracer(Tracer):
    """A tracer that does nothing. Useful for testing or disabling tracing."""

    def on_event(self, event: TraceEvent, context: dict[str, Any]) -> Any:
        pass


__all__ = [
    "Tracer",
    "NoOpTracer",
    "TraceEvent",
]
