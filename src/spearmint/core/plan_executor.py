"""Plan-based experiment executor.

This module provides execution of precomputed experiment plans,
running all paths in parallel and collecting results.
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar, copy_context
from dataclasses import dataclass, field
from typing import Any, TypeVar

from .context import BranchScope, RootScope, current_scope
from .introspection import ExperimentPath, ExperimentPlan

T = TypeVar("T")


# Context variable to track current path's config assignments
current_path_config: ContextVar[dict[str, str]] = ContextVar(
    "spearmint_path_config", default={}
)


@dataclass
class PathResult:
    """Result from executing a single path."""

    path_id: str
    config_assignments: dict[str, str]
    output: Any = None
    exception: Exception | None = None
    success: bool = True


@dataclass
class PlanExecutionResult:
    """Results from executing an entire plan."""

    path_results: list[PathResult] = field(default_factory=list)
    default_output: Any = None

    def as_records(self) -> list[dict[str, Any]]:
        """Format results as a list of records."""
        return [
            {
                "path_id": r.path_id,
                "config_chain": list(r.config_assignments.values()),
                "config_assignments": r.config_assignments,
                "output": r.output,
                "success": r.success,
                "exception": str(r.exception) if r.exception else None,
            }
            for r in self.path_results
        ]


class PlanExecutor:
    """Executes a precomputed experiment plan.

    Runs all paths in parallel (or via thread pool for sync functions),
    with each path using predetermined config assignments.
    """

    def __init__(
        self,
        plan: ExperimentPlan,
        func_registry: dict[str, Callable[..., Any]] | None = None,
        max_workers: int | None = None,
    ) -> None:
        """Initialize the plan executor.

        Args:
            plan: The precomputed experiment plan.
            func_registry: Optional mapping of function keys to callables.
                          If not provided, functions must be discovered at runtime.
            max_workers: Maximum number of threads for parallel execution.
        """
        self.plan = plan
        self.func_registry = func_registry or {}
        self.max_workers = max_workers

    async def execute(
        self,
        entry_func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> PlanExecutionResult:
        """Execute all paths in the plan.

        Args:
            entry_func: The entry point function to call for each path.
            *args: Positional arguments to pass to the entry function.
            **kwargs: Keyword arguments to pass to the entry function.

        Returns:
            PlanExecutionResult with all path outputs.
        """
        if not self.plan.paths:
            # No paths - just run the function directly
            result = await self._run_single(entry_func, {}, *args, **kwargs)
            return PlanExecutionResult(
                path_results=[result],
                default_output=result.output,
            )

        # Execute all paths concurrently
        tasks = []
        for path in self.plan.paths:
            task = asyncio.create_task(
                self._execute_path(entry_func, path, *args, **kwargs)
            )
            tasks.append(task)

        path_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        results: list[PathResult] = []
        for i, result in enumerate(path_results):
            if isinstance(result, Exception):
                results.append(
                    PathResult(
                        path_id=self.plan.paths[i].path_id,
                        config_assignments=self.plan.paths[i].config_assignments,
                        exception=result,
                        success=False,
                    )
                )
            else:
                results.append(result)

        # Default output is from first successful path
        default_output = None
        for r in results:
            if r.success:
                default_output = r.output
                break

        return PlanExecutionResult(
            path_results=results,
            default_output=default_output,
        )

    async def _execute_path(
        self,
        entry_func: Callable[..., Any],
        path: ExperimentPath,
        *args: Any,
        **kwargs: Any,
    ) -> PathResult:
        """Execute a single path with its config assignments."""
        # Set up context with path's config assignments
        token = current_path_config.set(path.config_assignments)

        try:
            result = await self._run_single(
                entry_func, path.config_assignments, *args, **kwargs
            )
            result.path_id = path.path_id
            result.config_assignments = path.config_assignments
            return result
        finally:
            current_path_config.reset(token)

    async def _run_single(
        self,
        func: Callable[..., Any],
        config_assignments: dict[str, str],
        *args: Any,
        **kwargs: Any,
    ) -> PathResult:
        """Run a function and capture its result."""
        path_id = "single"
        try:
            if inspect.iscoroutinefunction(func):
                output = await func(*args, **kwargs)
            else:
                # Run sync function in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                ctx = copy_context()
                with ThreadPoolExecutor(max_workers=1) as executor:
                    output = await loop.run_in_executor(
                        executor,
                        lambda: ctx.run(func, *args, **kwargs),
                    )

            return PathResult(
                path_id=path_id,
                config_assignments=config_assignments,
                output=output,
                success=True,
            )
        except Exception as e:
            return PathResult(
                path_id=path_id,
                config_assignments=config_assignments,
                exception=e,
                success=False,
            )


def get_assigned_config_id(func_key: str) -> str | None:
    """Get the config ID assigned to a function in the current path.

    This is used by experiment-decorated functions to look up their
    pre-assigned config ID instead of using runtime selection.

    Args:
        func_key: The function key (file:function_name).

    Returns:
        The assigned config ID, or None if not in a planned execution.
    """
    assignments = current_path_config.get()
    return assignments.get(func_key)


__all__ = [
    "PathResult",
    "PlanExecutionResult",
    "PlanExecutor",
    "current_path_config",
    "get_assigned_config_id",
]
