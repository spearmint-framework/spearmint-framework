"""Spearmint Framework.

A framework for experimentation with LLMs and document processing.
"""

import asyncio
from contextlib import asynccontextmanager
from contextvars import ContextVar
import inspect
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, AsyncGenerator, AsyncIterator

from pydantic import BaseModel

from spearmint.core.branch_strategy import BranchStrategy
from spearmint.core.config import Config, parse_configs
from spearmint.core.utils.handlers import yaml_handler
from spearmint.strategies import DefaultBranchStrategy
from experiment_enumerator import ExperimentEnumerator

global experiment_enumerator
experiment_enumerator = ExperimentEnumerator()

current_path_config: ContextVar[dict[str, str]] = ContextVar(
    "spearmint_path_config", default={}
)

class Spearmint:
    """Main Spearmint class for managing experiments and strategies."""

    def __init__(
        self,
        branch_strategy: type[BranchStrategy] | None = None,
        configs: list[dict[str, Any] | Config | str | Path] | None = None,
        bindings: dict[type[BaseModel], str] | None = None,
    ) -> None:
        self._config_handler: Callable[[str | Path], list[dict[str, Any]]] = yaml_handler
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
            experiment_enumerator.register_experiment(
                fn=func,
                main_handler=branch_strategy,
                background_handler=branch_strategy,
                configs=parsed_configs
            )

            @wraps(func)
            async def awrapper(*args: Any, **kwargs: Any) -> Any:
                async with Spearmint.run(func) as runner:
                    results = await runner(*args, **kwargs)
                    return results.main_result

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
    
    @staticmethod
    @asynccontextmanager
    async def run(func: Callable[..., Any]) -> AsyncIterator[Any]:
        """Run the given function as an experiment."""
        class Runner:
            def __init__(self, fn: Callable[..., Any], wait_for_variants: bool = False) -> None:
                self.main_config: dict[str, str] = {}
                self.variant_configs: list[dict[str, str]] = []
                self.main_result: Any = None
                self.variant_results: list[Any] = []
                self.wait_for_variants: bool = wait_for_variants
                self.fn = fn
            
            async def __call__(self, *args: Any, **kwargs: Any) -> Any:
                config_path = current_path_config.get()
                if config_path:
                    injected_args, injected_kwargs = self.config_di_handler(
                        self.fn, config_path, *args, **kwargs
                    )
                    if inspect.iscoroutinefunction(self.fn):
                        return await self.fn(*injected_args, **injected_kwargs)
                    else:
                        return self.fn(*injected_args, **injected_kwargs)
                
                tasks = []
                for config_path in experiment_enumerator.get_config_paths(self.fn.__name__):
                    token = current_path_config.set(config_path)
                    try:
                        if self.main_config == config_path:
                            self.main_result = await self(*args, **kwargs)
                        else:
                            tasks.append(self(*args, **kwargs))
                    finally:
                        current_path_config.reset(token)
                
                if self.wait_for_variants and tasks:
                    self.variant_results = await asyncio.gather(*tasks)

                return self

            async def __aenter__(self) -> "Runner":
                return self
            
            async def __aexit__(self, exc_type, exc, tb) -> None:
                pass

        yield Runner(func)



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
