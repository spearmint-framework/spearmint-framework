"""RunSession context manager for experiment execution.

This module provides the RunSession class which manages the lifecycle
of an experiment run, including scope management and result formatting.
"""

import asyncio
import inspect
from collections.abc import Callable
from typing import Any, TypeVar

from .context import BranchScope, RootScope, current_scope
from .result_formatter import format_branch_results

T = TypeVar("T")


class RunSession:
    """Async context manager for running experiments with full branch tracking.

    Provides an ergonomic API for running experiments and collecting results
    from all branches in a structured format.

    Example:
        >>> async with mint.run(main) as runner:
        ...     results = await runner(arg1="value1", arg2="value2")
        ...     # results contains all branch outputs with config chains
    """

    def __init__(
        self,
        func: Callable[..., Any],
        *,
        return_all: bool = True,
        wait_for_background: bool = True,
    ) -> None:
        """Initialize the RunSession.

        Args:
            func: The main function to execute within the experiment context.
            return_all: If True, return results from all branches. If False,
                       return only the default branch output.
            wait_for_background: If True, wait for background branches to complete
                                before returning results.
        """
        self.func = func
        self.return_all = return_all
        self.wait_for_background = wait_for_background
        self._root_scope: RootScope | None = None
        self._scope_token: Any = None
        self._background_tasks: list[asyncio.Task[Any]] = []

    async def __aenter__(self) -> "RunSession":
        """Enter the async context, setting up a fresh root scope."""
        self._root_scope = RootScope()
        self._scope_token = current_scope.set(self._root_scope)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the async context, cleaning up scope and background tasks."""
        try:
            if self.wait_for_background and self._background_tasks:
                # Wait for all background tasks to complete
                await asyncio.gather(*self._background_tasks, return_exceptions=True)
        finally:
            # Reset the scope
            if self._scope_token is not None:
                current_scope.reset(self._scope_token)

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the wrapped function and return formatted results.

        Args:
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            If return_all is True, returns a list of branch result records.
            If return_all is False, returns the default branch output.
        """
        # Create a session scope for this run
        session_scope = BranchScope(branch=None, parent=self._root_scope)
        session_scope.data["func"] = self.func.__name__
        session_scope.data["args"] = args
        session_scope.data["kwargs"] = kwargs
        
        if self._root_scope is not None:
            self._root_scope.children.append(session_scope)
        
        token = current_scope.set(session_scope)
        
        try:
            # Execute the function
            if inspect.iscoroutinefunction(self.func):
                result = await self.func(*args, **kwargs)
            else:
                result = self.func(*args, **kwargs)
            
            session_scope.data["output"] = result
            
            if self.return_all:
                # Format and return all branch results
                return format_branch_results(session_scope)
            else:
                # Return the raw result (default branch behavior)
                return result
        finally:
            current_scope.reset(token)
