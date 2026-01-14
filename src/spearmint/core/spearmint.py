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
from spearmint.core.run_session import RunSession
from spearmint.core.utils.handlers import jsonl_handler, yaml_handler
from spearmint.strategies import DefaultBranchStrategy


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
        self.evaluators: list[Callable[..., Any]] = evaluators or []

    def run(
        self,
        func: Callable[..., Any],
        *,
        return_all: bool = True,
        wait_for_background: bool = True,
    ) -> RunSession:
        """Create a RunSession context manager for executing an experiment.

        This provides an ergonomic API for running experiments and collecting
        results from all branches in a structured format.

        Args:
            func: The main function to execute within the experiment context.
            return_all: If True, return results from all branches formatted
                       as a list of records with config_chain and outputs.
                       If False, return only the default branch output.
            wait_for_background: If True, wait for background branches to
                                complete before returning results.

        Returns:
            A RunSession async context manager.

        Example:
            >>> async with mint.run(main) as runner:
            ...     results = await runner(
            ...         step1_input="example",
            ...         step2_input="data",
            ...     )
            ...     # results is a list of branch records
        """
        return RunSession(
            func=func,
            return_all=return_all,
            wait_for_background=wait_for_background,
        )

    def experiment(
        self,
        branch_strategy: type[BranchStrategy] | None = None,
        configs: list[dict[str, Any] | Config | str | Path] | None = None,
        bindings: dict[type[BaseModel], str] | None = None,
        evaluators: list[Callable[..., Any]] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for wrapping functions with experiment execution strategy."""
        evaluators = evaluators or self.evaluators

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return self.configure(
                branch_strategy=branch_strategy,
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
        bindings = bindings or self.bindings
        parsed_configs = parse_configs(configs or self.configs or [], yaml_handler)
        bindings = {Config: ""} if bindings is None else bindings

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def awrapper(*args: Any, **kwargs: Any) -> Any:
                branch_strategy_instance = branch_strategy(
                    func=func, configs=parsed_configs, bindings=bindings
                )
                return await branch_strategy_instance.run(*args, **kwargs)

            @wraps(func)
            def swrapper(*args: Any, **kwargs: Any) -> Any:
                import contextvars
                
                # Capture the current context to propagate to the async execution
                ctx = contextvars.copy_context()
                
                async def run_with_context() -> Any:
                    return await awrapper(*args, **kwargs)
                
                try:
                    loop = asyncio.get_running_loop()
                    # Already in an event loop - we need to run in the same loop
                    # Use asyncio.ensure_future and run until complete won't work
                    # Instead, we need to schedule and wait
                    import concurrent.futures
                    
                    def run_in_new_loop() -> Any:
                        # Run with copied context
                        return ctx.run(asyncio.run, run_with_context())
                    
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_new_loop)
                        return future.result()
                except RuntimeError:
                    # No running loop - run with context preserved
                    return ctx.run(asyncio.run, run_with_context())

            return awrapper if inspect.iscoroutinefunction(func) else swrapper

        return decorator


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
