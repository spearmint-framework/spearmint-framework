"""Spearmint Framework.

A framework for experimentation with LLMs and document processing.
"""

import asyncio
import inspect
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from spearmint.core import BranchStrategy, Config
from spearmint.core.config import parse_configs
from spearmint.core.utils.handlers import jsonl_handler, yaml_handler
from spearmint.strategies import DefaultBranchStrategy
from spearmint.core.trace import fn_memo


class Spearmint:
    """Main Spearmint class for managing experiments and strategies."""

    def __init__(
        self,
        branch_strategy: type[BranchStrategy] | None = None,
        configs: list[dict[str, Any] | Config | str | Path] | None = None,
        bindings: dict[type[BaseModel], str] | None = None,
        evaluators: list[Callable[..., Any]] | None = None,
    ) -> None:
        self._config_handler: Callable[[str | Path], list[dict[str, Any]]] = yaml_handler
        self._dataset_handler: Callable[[str | Path], list[dict[str, Any]]] = jsonl_handler
        self.branch_strategy: type[BranchStrategy] = branch_strategy or DefaultBranchStrategy
        self.configs: list[Config] = parse_configs(configs or [], self._config_handler)
        self.bindings: dict[type[BaseModel], str] = {Config: ""} if bindings is None else bindings

    def experiment(
        self,
        branch_strategy: type[BranchStrategy] | None = None,
        configs: list[dict[str, Any] | Config | str | Path] | None = None,
        bindings: dict[type[BaseModel], str] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for wrapping functions with experiment execution strategy."""
        branch_strategy = branch_strategy or self.branch_strategy
        bindings = bindings or self.bindings
        parsed_configs = parse_configs(configs or self.configs or [], yaml_handler)
        bindings = {Config: ""} if bindings is None else bindings

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def awrapper(*args: Any, **kwargs: Any) -> Any:
                memo_dict = fn_memo.get()
                if func.__name__ in memo_dict:
                    print(f"Using memoized result for {func.__name__}: {memo_dict[func.__name__]}")
                    return memo_dict[func.__name__]
                branch_strategy_instance = branch_strategy(
                    func=func, configs=parsed_configs, bindings=bindings
                )
                return await branch_strategy_instance.run(*args, **kwargs)

            @wraps(func)
            def swrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    loop = asyncio.get_running_loop()
                    return loop.run_until_complete(awrapper(*args, **kwargs))
                except RuntimeError:
                    # No running loop, create one but preserve context
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(awrapper(*args, **kwargs))
                    finally:
                        loop.close()
                        asyncio.set_event_loop(None)

            return awrapper if inspect.iscoroutinefunction(func) else swrapper

        return decorator

    def run(
        self, func: Callable[..., Any], dataset: list[dict[str, Any]] | Path | str
    ) -> list[dict[str, Any]]:
        """Run a function with the loaded dataset and configurations.

        Args:
            func: The function to run.
            dataset: The dataset to process, either as a list of dictionaries or a file path.
        """

        if isinstance(dataset, (str, Path)):
            dataset = self._dataset_handler(dataset)

        output_dataset: list[dict[str, Any]] = []



        return output_dataset


def experiment(
    branch_strategy: type[BranchStrategy],
    configs: list[dict[str, Any] | Config | str | Path],
    bindings: dict[type[BaseModel], str] | None = None,
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
    spearmint_instance = Spearmint(
        branch_strategy=branch_strategy,
        configs=configs,
        bindings=bindings,
    )
    return spearmint_instance.experiment()

