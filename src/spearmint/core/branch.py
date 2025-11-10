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

from enum import Enum
import time
import traceback as tb
from collections.abc import Iterator, Sequence
from typing import Any, Callable, TypeVar
import inspect

from pydantic import BaseModel

from .dependency_injector import inject_config
from .run_wrapper import RunWrapper


class BranchExecType(Enum):
    """Enumeration of branch execution types."""
    PARALLEL = "parallel"      # Execute branches concurrently
    SEQUENTIAL = "sequential"  # Execute branches one after another on main thread
    BACKGROUND = "background"  # Execute on background thread(s)
    NOOP = "noop"              # No operation

class Branch(RunWrapper):
    """Represents a single execution branch of an experiment.

    A Branch tracks the configuration, execution timing, status, output,
    and any exceptions that occur during the execution of an experiment variant.
    """
    default: bool = False

    def __init__(self, func: Callable[..., Any], configs: list[BaseModel]) -> None:
        self.func = func
        self.config_di_handler = inject_config
        self.configs = configs
        self.exec_type: BranchExecType = BranchExecType.PARALLEL

    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the branch with dependency-injected config."""
        async with self.wrapped():
            injected_args, injected_kwargs = self.config_di_handler(self.func, self.configs, *args, **kwargs)
            if inspect.iscoroutinefunction(self.func):
                result = await self.func(*injected_args, **injected_kwargs)
            else:
                result = self.func(*injected_args, **injected_kwargs)
            self.output = result

        return self.output

__all__ = ["Branch"]
