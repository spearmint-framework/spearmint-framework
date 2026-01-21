"""Spearmint Framework.

A framework for experimentation with LLMs and document processing.
"""

from __future__ import annotations

import asyncio
import inspect
from contextlib import asynccontextmanager
from collections.abc import Callable, Sequence
from functools import wraps
from pathlib import Path
from typing import Any

from .configuration import Config, parse_configs
from .experiment_function import ExperimentFunction
from .registry import experiment_fn_registry
from .runner import run_experiment
from .utils.handlers import yaml_handler

class Spearmint:
    """Main Spearmint class for managing experiments and strategies."""

    def __init__(
        self,
        branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = None,
        configs: list[dict[str, Any] | Config | str | Path] | None = None,
    ) -> None:
        self.branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = branch_strategy
        self.configs: list[Config] = parse_configs(configs or [], yaml_handler)

    def experiment(
        self,
        branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = None,
        configs: list[dict[str, Any] | Config | str | Path] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for wrapping functions with experiment execution strategy."""
        branch_strategy = branch_strategy or self.branch_strategy
        parsed_configs = parse_configs(configs or self.configs or [], yaml_handler)

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            experiment = ExperimentFunction(func=func, configs=parsed_configs)
            experiment_fn_registry.register_experiment(experiment)

            @wraps(func)
            async def awrapper(*args: Any, **kwargs: Any) -> Any:
                async with run_experiment(func) as runner:
                    results = await runner(*args, **kwargs)
                    return results.main_result.result

            @wraps(func)
            def swrapper(*args: Any, **kwargs: Any) -> Any:
                import contextvars

                ctx = contextvars.copy_context()

                async def run_with_context() -> Any:
                    return await awrapper(*args, **kwargs)

                try:
                    loop = asyncio.get_running_loop()
                    _ = loop
                    import concurrent.futures

                    def run_in_new_loop() -> Any:
                        return ctx.run(asyncio.run, run_with_context())

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_new_loop)
                        return future.result()
                except RuntimeError:
                    return ctx.run(asyncio.run, run_with_context())

            return awrapper if inspect.iscoroutinefunction(func) else swrapper

        return decorator
    
    @staticmethod
    @asynccontextmanager
    async def run(func: Callable[..., Any], await_background_cases: bool = False):
        """Run the given function as an experiment."""
        async with run_experiment(func, await_background_cases=await_background_cases) as runner:
            yield runner


def experiment(
    configs: Sequence[dict[str, Any] | Config | str | Path],
    branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for wrapping functions with experiment execution strategy."""

    spearmint_instance = Spearmint(
        configs=list(configs),
        branch_strategy=branch_strategy,
    )
    return spearmint_instance.experiment()
