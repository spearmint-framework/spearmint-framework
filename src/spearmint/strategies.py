"""Strategy implementations for experiment execution orchestration.

This module provides the Strategy protocol and built-in strategy implementations
for coordinating multi-config experiment execution with different patterns.

Acceptance Criteria Reference: Section 2.5 (Strategy Layer)
- Strategy protocol with async run method
- RoundRobinStrategy for sequential config rotation
- ShadowStrategy for primary execution with background shadowing
- MultiBranchStrategy for concurrent execution of all configs
"""

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from typing import Any, Optional, Protocol

from .branch import Branch, BranchContainer
from .logging import LoggerBackend


class Strategy(Protocol):
    """Protocol defining the interface for experiment execution strategies."""

    async def run(
        self,
        func: Callable[..., Awaitable[Any]],
        configs: Sequence[dict[str, Any]],
        *args: Any,
        logger: Optional[LoggerBackend] = None,
        **kwargs: Any,
    ) -> Any:
        """Execute the experiment function with the given configs.

        Args:
            func: Async function to execute (should accept config kwarg)
            configs: Sequence of configuration dictionaries
            *args: Positional arguments to pass to func
            logger: Optional logger backend for tracking
            **kwargs: Keyword arguments to pass to func

        Returns:
            Strategy-specific return value (direct result, BranchContainer, etc.)
        """
        ...


async def _execute_branch(
    func: Callable[..., Awaitable[Any]],
    config: dict[str, Any],
    config_id: str,
    logger: Optional[LoggerBackend],
    *args: Any,
    **kwargs: Any,
) -> Branch:
    """Execute function with a single config and return a Branch with results.

    This helper manages the full branch lifecycle: creation, execution,
    logging, and status tracking.

    Args:
        func: Async function to execute
        config: Configuration dictionary for this execution
        config_id: Unique identifier for this config
        logger: Optional logger backend
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        Branch instance with execution results
    """
    branch = Branch.start(config_id, config)

    # Start run and log parameters
    if logger is not None:
        logger.start_run(config_id)
        logger.log_params(config_id, config)

    try:
        # Execute function with config
        result = await func(*args, config=config, **kwargs)
        branch.mark_success(result)

        # Log success metrics
        if logger is not None and branch.duration is not None:
            logger.log_metrics(config_id, {"duration": branch.duration})

    except Exception as exc:
        # Capture failure
        branch.mark_failure(exc)

        # Log failure metrics
        if logger is not None and branch.duration is not None:
            logger.log_metrics(config_id, {"duration": branch.duration})

    finally:
        # Log the completed branch
        if logger is not None:
            logger.log_branch(config_id, branch)
            logger.end_run(config_id)

    return branch


class RoundRobinStrategy:
    """Strategy that cycles through configs sequentially on each execution.

    Maintains an internal index that rotates through the config list,
    executing one config per call and returning its output directly.
    """

    def __init__(self) -> None:
        """Initialize the round-robin strategy."""
        self._index = 0

    async def run(
        self,
        func: Callable[..., Awaitable[Any]],
        configs: Sequence[dict[str, Any]],
        *args: Any,
        logger: Optional[LoggerBackend] = None,
        **kwargs: Any,
    ) -> Any:
        """Execute function with the next config in rotation.

        Args:
            func: Async function to execute
            configs: Sequence of configuration dictionaries
            *args: Positional arguments to pass to func
            logger: Optional logger backend
            **kwargs: Keyword arguments to pass to func

        Returns:
            Direct output from the executed function

        Raises:
            ValueError: If configs is empty
        """
        if not configs:
            raise ValueError("RoundRobinStrategy requires at least one config")

        # Select config using current index
        config = configs[self._index]
        config_id = f"round_robin_{self._index}"

        # Execute with selected config
        branch = await _execute_branch(func, config, config_id, logger, *args, **kwargs)

        # Advance index for next call
        self._index = (self._index + 1) % len(configs)

        # Re-raise exception if execution failed
        if branch.status == "failed" and branch.exception_info is not None:
            # Reconstruct exception for propagation
            exc_type = branch.exception_info["type"]
            exc_message = branch.exception_info["message"]
            raise RuntimeError(f"{exc_type}: {exc_message}")

        return branch.output


class ShadowStrategy:
    """Strategy that executes primary config foreground, others as shadows.

    Returns the primary config result immediately while scheduling shadow
    executions in the background for comparison/testing purposes.
    """

    def __init__(self, primary_index: int = 0) -> None:
        """Initialize the shadow strategy.

        Args:
            primary_index: Index of the primary config (default: 0)
        """
        self.primary_index = primary_index
        self._shadow_tasks: list[asyncio.Task[Branch]] = []

    async def run(
        self,
        func: Callable[..., Awaitable[Any]],
        configs: Sequence[dict[str, Any]],
        *args: Any,
        logger: Optional[LoggerBackend] = None,
        **kwargs: Any,
    ) -> Any:
        """Execute primary config foreground, schedule shadows in background.

        Args:
            func: Async function to execute
            configs: Sequence of configuration dictionaries
            *args: Positional arguments to pass to func
            logger: Optional logger backend
            **kwargs: Keyword arguments to pass to func

        Returns:
            Direct output from the primary config execution

        Raises:
            ValueError: If configs is empty or primary_index out of range
        """
        if not configs:
            raise ValueError("ShadowStrategy requires at least one config")
        if self.primary_index >= len(configs):
            raise ValueError(
                f"Primary index {self.primary_index} out of range for {len(configs)} configs"
            )

        # Execute primary config
        primary_config = configs[self.primary_index]
        primary_config_id = f"shadow_primary_{self.primary_index}"
        primary_branch = await _execute_branch(
            func, primary_config, primary_config_id, logger, *args, **kwargs
        )

        # Schedule shadow configs as background tasks
        self._shadow_tasks = []
        for i, config in enumerate(configs):
            if i != self.primary_index:
                config_id = f"shadow_{i}"
                task = asyncio.create_task(
                    _execute_branch(func, config, config_id, logger, *args, **kwargs)
                )
                self._shadow_tasks.append(task)

        # Re-raise exception if primary execution failed
        if primary_branch.status == "failed" and primary_branch.exception_info is not None:
            exc_type = primary_branch.exception_info["type"]
            exc_message = primary_branch.exception_info["message"]
            raise RuntimeError(f"{exc_type}: {exc_message}")

        return primary_branch.output

    async def gather_shadows(self) -> list[Branch]:
        """Await all shadow task completions and return their branches.

        This is a test/utility method to explicitly wait for all shadow
        executions to complete.

        Returns:
            List of Branch instances from shadow executions
        """
        if not self._shadow_tasks:
            return []
        return await asyncio.gather(*self._shadow_tasks, return_exceptions=False)


class MultiBranchStrategy:
    """Strategy that executes all configs concurrently.

    Fans out execution across all configs in parallel and returns a
    BranchContainer with all results.
    """

    async def run(
        self,
        func: Callable[..., Awaitable[Any]],
        configs: Sequence[dict[str, Any]],
        *args: Any,
        logger: Optional[LoggerBackend] = None,
        **kwargs: Any,
    ) -> BranchContainer:
        """Execute function concurrently with all configs.

        Args:
            func: Async function to execute
            configs: Sequence of configuration dictionaries
            *args: Positional arguments to pass to func
            logger: Optional logger backend
            **kwargs: Keyword arguments to pass to func

        Returns:
            BranchContainer with all execution results

        Raises:
            ValueError: If configs is empty
        """
        if not configs:
            raise ValueError("MultiBranchStrategy requires at least one config")

        # Create tasks for all configs
        tasks = []
        for i, config in enumerate(configs):
            config_id = f"multi_branch_{i}"
            task = _execute_branch(func, config, config_id, logger, *args, **kwargs)
            tasks.append(task)

        # Execute all concurrently
        branches = await asyncio.gather(*tasks, return_exceptions=False)

        return BranchContainer(list(branches))


__all__ = [
    "Strategy",
    "RoundRobinStrategy",
    "ShadowStrategy",
    "MultiBranchStrategy",
]
