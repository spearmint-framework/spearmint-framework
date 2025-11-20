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

import asyncio
import inspect
from collections.abc import Callable
from enum import Enum
from typing import Any

from pydantic import BaseModel

from .trace import trace_manager, fn_memo
from .dependency_injector import inject_config
from .run_wrapper import RunWrapper


class BranchExecType(Enum):
    """Enumeration of branch execution types."""

    PARALLEL = "parallel"  # Execute branches concurrently
    SEQUENTIAL = "sequential"  # Execute branches one after another on main thread
    BACKGROUND = "background"  # Execute on background thread(s)
    NOOP = "noop"  # No operation


class Branch(RunWrapper):
    """Represents a single execution branch of an experiment.

    A Branch tracks the configuration, execution timing, status, output,
    and any exceptions that occur during the execution of an experiment variant.
    """

    default: bool = False

    def __init__(self, func: Callable[..., Any], config_id: str, configs: list[BaseModel]) -> None:
        self.func = func
        self.config_di_handler = inject_config
        self.config_id = config_id
        self.configs = configs
        self.exec_type: BranchExecType = BranchExecType.PARALLEL

    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the branch with dependency-injected config."""
        result: Any | None = None
        async with self.wrapped():
            with trace_manager.start_trace(name="branch") as trace:
                trace.data["func"] = self.func.__name__
                trace.data["config_id"] = self.config_id
                injected_args, injected_kwargs = self.config_di_handler(
                    self.func, self.configs, *args, **kwargs
                )
                trace.data["args"] = injected_args
                trace.data["kwargs"] = injected_kwargs
                if inspect.iscoroutinefunction(self.func):
                    result = await self.func(*injected_args, **injected_kwargs)
                else:
                    result = self.func(*injected_args, **injected_kwargs)
                trace.data["return_value"] = result
                # TODO: Improve this with event loop hooks if possible
                await asyncio.sleep(0.1)  # Yield control to allow trace export processing
                child_branches = [b for b in trace.children if b.name == "branch"]

            for child in child_branches[1:]:
                print(f"Processing child branch trace: {child.data['func']} -> {child.data.get('return_value')}")
                with trace_manager.start_trace(name="branch") as trace:
                    trace.data["func"] = self.func.__name__
                    trace.data["config_id"] = self.config_id
                    trace.data["args"] = injected_args
                    trace.data["kwargs"] = injected_kwargs
                    token = fn_memo.set({
                        child.data["func"]: child.data.get("return_value")
                    })
                    if inspect.iscoroutinefunction(self.func):
                        result = await self.func(*injected_args, **injected_kwargs)
                    else:
                        result = self.func(*injected_args, **injected_kwargs)
                    fn_memo.reset(token)
                    trace.data["return_value"] = result


            self.output = result

        return self.output


__all__ = ["Branch"]
