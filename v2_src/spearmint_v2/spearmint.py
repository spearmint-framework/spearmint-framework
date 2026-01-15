"""Spearmint Framework.

A framework for experimentation with LLMs and document processing.
"""

import asyncio
from contextlib import asynccontextmanager
from contextvars import ContextVar
import inspect
from collections.abc import Callable, Sequence
from functools import wraps
from pathlib import Path
from typing import Annotated, Any, AsyncIterator

from pydantic import BaseModel

from .configuration import Config, parse_configs
from .experiment_enumerator import ConfigPath, ExperimentEnumerator, Experiment, inject_config
from .utils.handlers import yaml_handler

global experiment_enumerator
experiment_enumerator = ExperimentEnumerator()

current_path_config: ContextVar[ConfigPath | None] = ContextVar(
    "spearmint_path_config", default=None
)

class Spearmint:
    """Main Spearmint class for managing experiments and strategies."""

    def __init__(
        self,
        branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = None,
        configs: list[dict[str, Any] | Config | str | Path] | None = None,
        bindings: dict[type[BaseModel], str] | None = None,
    ) -> None:
        self._config_handler: Callable[[str | Path], list[dict[str, Any]]] = yaml_handler
        self.branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = branch_strategy
        self.configs: list[Config] = parse_configs(configs or [], self._config_handler)
        self.bindings: dict[type[BaseModel], str] = {Config: ""} if bindings is None else bindings

    def experiment(
        self,
        branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = None,
        configs: list[dict[str, Any] | Config | str | Path] | None = None,
        bindings: dict[type[BaseModel], str] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for wrapping functions with experiment execution strategy."""
        branch_strategy = branch_strategy or self.branch_strategy
        bindings = bindings or self.bindings
        parsed_configs = parse_configs(configs or self.configs or [], yaml_handler)
        bindings = {Config: ""} if bindings is None else bindings

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            experiment = Experiment(func=func, configs=parsed_configs)
            experiment_enumerator.register_experiment(experiment)

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
    async def run(func: Callable[..., Any], wait_for_variants: bool = False) -> AsyncIterator["Spearmint.run.Runner"]:
        """Run the given function as an experiment."""
        class Runner:
            def __init__(self, func: Callable[..., Any], main_config: ConfigPath, variant_configs: list[ConfigPath] = [], wait_for_variants: bool = False) -> None:
                self.main_config: ConfigPath = main_config
                self.variant_configs: list[ConfigPath] = variant_configs
                self.main_result: Any = None
                self.variant_results: list[Any] = []
                self.wait_for_variants: bool = wait_for_variants
                self.func = func
            
            async def __call__(self, *args: Any, **kwargs: Any) -> Any:
                configs = self.main_config.bound_configs.get(self.func.__qualname__, [])
                injected_args, injected_kwargs = inject_config(
                    self.func, configs, *args, **kwargs
                )
                if inspect.iscoroutinefunction(self.func):
                    self.main_result = await self.func(*injected_args, **injected_kwargs)
                else:
                    self.main_result = self.func(*injected_args, **injected_kwargs)
                
                tasks = []

                for variant_config in self.variant_configs:
                    async def run_variant(config: ConfigPath) -> Any:
                        token = current_path_config.set(config)
                        try:
                            return await Runner(self.func, main_config=config)(*args, **kwargs)
                        finally:
                            current_path_config.reset(token)
                    task = asyncio.create_task(run_variant(variant_config))
                    tasks.append(task)
                
                if self.wait_for_variants and tasks:
                    self.variant_results = [r.main_result for r in await asyncio.gather(*tasks)]

                return self

            async def __aenter__(self) -> "Runner":
                return self
            
            async def __aexit__(self, exc_type, exc, tb) -> None:
                pass

        config_path = current_path_config.get()
        if config_path:
            yield Runner(func, main_config=config_path)
        else:
            main_config, variant_configs = experiment_enumerator.get_config_paths(func)
            yield Runner(func, main_config=main_config, variant_configs=variant_configs, wait_for_variants=wait_for_variants)



def experiment(
    branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = None,
    configs: Sequence[dict[str, Any] | Config | str | Path] | None = None,
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
