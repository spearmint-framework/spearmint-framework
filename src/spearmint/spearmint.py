"""Spearmint Framework.

A framework for experimentation with LLMs and document processing.
"""

from __future__ import annotations

import asyncio
import inspect
from contextlib import asynccontextmanager, contextmanager
from collections.abc import Callable, Sequence
from functools import wraps
from pathlib import Path
from typing import Any, ParamSpec, TypeVar, cast

from .configuration import Config, parse_configs
from .experiment_function import ExperimentFunction
from .registry import experiment_fn_registry
from .runner import run_experiment, run_experiment_async
from .utils.handlers import yaml_handler

T = TypeVar("T")


class Spearmint:
    """Main Spearmint class for managing experiments and strategies."""

    def __init__(
        self,
        branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = None,
        configs: Sequence[dict[str, Any] | Config | str | Path] | None = None,
    ) -> None:
        self.branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = branch_strategy
        self.configs: list[Config] = parse_configs(configs or [], yaml_handler)

    def experiment(
        self,
        branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = None,
        configs: Sequence[dict[str, Any] | Config | str | Path] | None = None,
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Decorator for wrapping functions with experiment execution strategy."""
        branch_strategy = branch_strategy or self.branch_strategy
        parsed_configs = parse_configs(configs or self.configs or [], yaml_handler)

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            experiment = ExperimentFunction(func=func, configs=parsed_configs, config_handler=branch_strategy)
            experiment_fn_registry.register_experiment(experiment)

            @wraps(func)
            def swrapper(*args: Any, **kwargs: Any) -> T:
                with run_experiment(func) as runner:
                    results = runner(*args, **kwargs)
                    return cast(T, results.main_result.result)

            @wraps(func)
            async def awrapper(*args: Any, **kwargs: Any) -> T:
                async with run_experiment_async(func) as runner:
                    results = await runner(*args, **kwargs)
                    return cast(T, results.main_result.result)

            return awrapper if inspect.iscoroutinefunction(func) else swrapper

        return decorator
    
    @staticmethod
    @contextmanager
    def run(func: Callable[..., Any], await_variants: bool = False):
        """Run the given function as a sync experiment."""
        with run_experiment(func, await_variants=await_variants) as runner:
            yield runner

    @staticmethod
    @asynccontextmanager
    async def arun(func: Callable[..., Any], await_variants: bool = False):
        """Run the given function as an async experiment."""
        async with run_experiment_async(
            func, await_variants=await_variants
        ) as runner:
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
