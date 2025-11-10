"""Spearmint Framework.

A framework for experimentation with LLMs and document processing.
"""

import asyncio
import inspect
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from functools import wraps
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from spearmint.core import BranchStrategy, Config
from spearmint.core.config import parse_configs
from spearmint.core.utils.handlers import jsonl_handler, yaml_handler
from spearmint.strategies import DefaultBranchStrategy


class Spearmint:
    """Main Spearmint class for managing experiments and strategies."""

    def __init__(
        self,
        branch_strategy: type[BranchStrategy] | None = None,
        configs: list[dict[str, Any] | Config] | None = None,
        bindings: dict[type[BaseModel], str] | None = None,
        evaluators: list[Callable[..., Any]] | None = None,
    ) -> None:
        self._config_handler: Callable[[str | Path], list[dict[str, Any]]] = yaml_handler
        self._dataset_handler: Callable[[str | Path], list[dict[str, Any]]] = jsonl_handler
        self.branch_strategy: type[BranchStrategy] = branch_strategy or DefaultBranchStrategy
        self.configs: list[Config] = parse_configs(configs or [], self._config_handler)
        self.bindings: dict[type[BaseModel], str] = {Config: ""} if bindings is None else bindings
        self.evaluators: list[Callable[..., Any]] = evaluators or []

    def experiment(
        self,
        strategy: type[BranchStrategy] | None = None,
        configs: list[dict[str, Any] | Config | str | Path] | None = None,
        bindings: dict[type[BaseModel], str] | None = None,
        evaluators: list[Callable[..., Any]] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for wrapping functions with experiment execution strategy."""
        evaluators = evaluators or self.evaluators

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return self.configure(
                strategy=strategy,
                configs=configs,
                bindings=bindings,
            )(func)

        return decorator
    
    def configure(
        self,
        branch_strategy: type[BranchStrategy] | None = None,
        configs: list[dict[str, Any] | Config | str | Path] | None = None,
        bindings: dict[type[BaseModel], str] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for wrapping functions with experiment execution strategy."""
        branch_strategy = branch_strategy or self.branch_strategy
        configs = configs or self.configs
        bindings = bindings or self.bindings
        configs = parse_configs(configs or [], yaml_handler)
        bindings = {Config: ""} if bindings is None else bindings

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def awrapper(*args: Any, **kwargs: Any) -> Any:
                branch_strategy_instance = branch_strategy(func=func, configs=configs, bindings=bindings)
                return await branch_strategy_instance.run(*args, **kwargs)

            @wraps(func)
            def swrapper(*args: Any, **kwargs: Any) -> Any:
                result = ThreadPoolExecutor().submit(lambda: asyncio.run(awrapper(*args, **kwargs)))
                r = result.result()
                return r

            return awrapper if inspect.iscoroutinefunction(func) else swrapper

        return decorator
    

    def run(
        self, func: Callable[..., Any], dataset: list[dict[str, Any]] | Path | str
    ) -> list[dict[str, Any]]:
        """Run a function with the loaded dataset and configurations.

        Args:
            func: The function to run.
            skip_eval: If True, skip evaluation after running the experiment.
        """
        # # Error if func is not decorated with @experiment
        # if not getattr(func, "spearmint_experiment", False):
        #     raise ValueError("Function must be decorated with @experiment")

        if isinstance(dataset, (str, Path)):
            dataset = self._dataset_handler(dataset)

        output_dataset = []
        # for data_line in dataset:
        #     kwargs = {}
        #     for param in inspect.signature(func).parameters.keys():
        #         if param in data_line:
        #             kwargs[param] = data_line[param]

        #     if inspect.iscoroutinefunction(func):
        #         try:
        #             loop = asyncio.get_running_loop()
        #             result = loop.run_until_complete(func(**kwargs))
        #         except RuntimeError:
        #             result = asyncio.run(func(**kwargs))
        #     else:
        #         result = func(**kwargs)

        #     output_data_line = deepcopy(data_line)
        #     if isinstance(result, BranchContainer):
        #         for branch in result.branches:
        #             data_line_branch = deepcopy(output_data_line)
        #             data_line_branch["output"] = branch.output
        #             data_line_branch["config_id"] = branch.config_id
        #             output_dataset.append(data_line_branch)
        #     else:
        #         output_data_line["output"] = result
        #         output_dataset.append(output_data_line)

        return output_dataset
    
    # def configure(
    #     self,
    #     branch_strategy: type[BranchStrategy] | None = None,
    #     configs: list[dict[str, Any] | Config] | None = None,
    #     bindings: dict[type[BaseModel], str] | None = None,
    # ) -> None:
    #     """Configure the Spearmint instance with new settings."""

    #     executor = ThreadPoolExecutor()
    #     configs = parse_configs(configs or [], self._config_handler)
    #     bindings = {Config: ""} if bindings is None else bindings


    #     strategy_instance = branch_strategy(
    #         configs=configs,
    #         bindings=bindings,
    #     )

    #     def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    #         @wraps(func)
    #         async def awrapper(*args: Any, **kwargs: Any) -> Any:
    #             return await strategy_instance.run(func, *args, **kwargs)

    #         @wraps(func)
    #         def swrapper(*args: Any, **kwargs: Any) -> Any:
    #             result = executor.submit(lambda: asyncio.run(awrapper(*args, **kwargs)))
    #             return result.result()

    #         return awrapper if inspect.iscoroutinefunction(func) else swrapper

    #     return decorator


def experiment(
    branch_strategy: type[BranchStrategy],
    configs: list[dict[str, Any] | Config | str | Path],
    bindings: dict[type[BaseModel], str] | None = None,
    evaluators: list[Callable[..., Any]] | None = None,
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
        evaluators=evaluators,
    )
    return spearmint_instance.experiment()

def configure(
    branch_strategy: type[BranchStrategy],
    configs: list[dict[str, Any] | Config],
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
        >>> @configure()
        >>> async def my_func(x: int, config: dict) -> int:
        ...     return x + config['delta']
        >>>
        >>> result = await my_func(10)
    """
    spearmint_instance = Spearmint()
    return spearmint_instance.configure(
        branch_strategy=branch_strategy,
        configs=configs,
        bindings=bindings,
    )