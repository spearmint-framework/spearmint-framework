"""Experiment decorator and orchestration.

This module provides the @experiment decorator for wrapping async functions
with multi-branch execution strategies and config pool management.

Acceptance Criteria Reference: Section 2.6 (Experiment Decorator)
- @experiment decorator wrapping async functions
- Strategy delegation and config pool injection
- Inspection hooks for accessing branch results
"""

import asyncio
import functools
from collections.abc import Callable
from typing import Any, Optional

from .logging import LoggerBackend
from .strategies import Strategy


def experiment(strategy: Strategy) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for wrapping functions with experiment execution strategy.

    This decorator wraps an async function and orchestrates its execution
    through the provided strategy, handling config injection and logging.

    Args:
        strategy: Strategy instance to use for execution

    Returns:
        Decorator function

    Example:
        >>> @experiment(RoundRobinStrategy())
        >>> async def my_func(x: int, config: dict) -> int:
        ...     return x + config['delta']
        >>>
        >>> result = await my_func(10, configs=[{'delta': 1}, {'delta': 2}])
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Ensure function is async
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(
                f"Function '{func.__name__}' must be async. Use 'async def' to define the function."
            )

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract configs from kwargs
            configs = kwargs.pop("configs", None)
            if configs is None:
                raise ValueError(
                    f"'{func.__name__}' requires 'configs' keyword argument "
                    "for experiment execution"
                )

            # Extract optional logger
            logger: Optional[LoggerBackend] = kwargs.pop("logger", None)

            # Delegate to strategy
            return await strategy.run(func, configs, *args, logger=logger, **kwargs)

        return wrapper

    return decorator


__all__ = ["experiment"]
