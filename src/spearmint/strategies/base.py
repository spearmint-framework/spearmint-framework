"""Base strategy protocol and branch execution helper.

Defines the `Strategy` Protocol that all execution strategies must implement,
along with the internal `_execute_branch` helper used by concrete strategies to
perform a single branch execution and logging lifecycle.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Sequence
from typing import Any, Protocol

from ..branch import Branch
from ..logging import LoggerBackend


class Strategy(Protocol):
    """Protocol defining the interface for experiment execution strategies."""

    async def run(
        self,
        func: Callable[..., Awaitable[Any]],
        configs: Sequence[dict[str, Any]],
        *args: Any,
        logger: LoggerBackend | None = None,
        **kwargs: Any,
    ) -> Any:  # pragma: no cover - protocol definition only
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
    logger: LoggerBackend | None,
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
    print(f"Starting branch {config_id}")

    if logger is not None:
        logger.start_run(config_id)
        logger.log_params(config_id, config)

    try:
        if inspect.iscoroutinefunction(func):
            result = await func(*args, config=config, **kwargs)
        else:
            result = func(*args, config=config, **kwargs)
        branch.mark_success(result)
        if logger is not None and branch.duration is not None:
            logger.log_metrics(config_id, {"duration": branch.duration})
    except Exception as exc:  # noqa: BLE001 - broad to capture and store exception
        branch.mark_failure(exc)
        if logger is not None and branch.duration is not None:
            logger.log_metrics(config_id, {"duration": branch.duration})
    finally:
        if logger is not None:
            logger.log_branch(config_id, branch)
            logger.end_run(config_id)

    return branch


__all__ = ["Strategy", "_execute_branch"]
