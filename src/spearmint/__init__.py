"""Spearmint Framework.

A framework for experimentation with LLMs and document processing.
"""

import asyncio
import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any

from .branch import Branch, BranchContainer
from .strategies import Strategy

# from .experiment import experiment as experiment_decorator
__version__ = "0.1.0"


class Spearmint:
    """Main Spearmint class for managing experiments and strategies."""

    def __init__(self) -> None:
        self.strategy: Strategy | None = None
        self.configs: list[dict[str, Any]] = []

    def get_config(self) -> dict[str, Any]:
        """Get the next configuration from the config pool."""
        return {}

    def set_strategy(self, strategy: Strategy) -> None:
        """Set the experiment execution strategy."""
        self.strategy = strategy

    def experiment(
        self, strategy: Strategy | None = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for wrapping functions with experiment execution strategy.

        This decorator wraps an async function and orchestrates its execution
        through the provided strategy, handling config injection and logging.

        Args:
            strategy: Strategy instance to use for execution

        Returns:
            Decorator function

        Example:
            >>> @experiment()
            >>> async def my_func(x: int, config: dict) -> int:
            ...     return x + config['delta']
            >>>
            >>> result = await my_func(10)
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def awrapper(*args: Any, **kwargs: Any) -> Any:
                selected_strategy = strategy or self.strategy
                if selected_strategy is None:
                    raise ValueError("Experiment strategy is not set. Use 'set_strategy' first.")
                return await selected_strategy.run(func, self.configs, *args, **kwargs)

            @wraps(func)
            def swrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                return loop.run_until_complete(awrapper(*args, **kwargs))

            return awrapper if inspect.iscoroutinefunction(func) else swrapper

        return decorator


__all__ = ["__version__", "Branch", "BranchContainer", "Spearmint"]
