"""Spearmint Framework.

A framework for experimentation with LLMs and document processing.
"""

import asyncio
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass
import inspect
from collections.abc import AsyncGenerator, Callable, Sequence
from functools import wraps
from pathlib import Path
from types import CoroutineType
from typing import Any, AsyncIterator

from pydantic import BaseModel

from .configuration import Config, parse_configs
from .experiment_function import ExperimentCase, ExperimentFunctionRegistry, ExperimentFunction
from .utils.handlers import yaml_handler

global experiment_fn_registry
experiment_fn_registry = ExperimentFunctionRegistry()

current_experiment_case: ContextVar[ExperimentCase | None] = ContextVar(
    "spearmint_experiment_case", default=None
)


@dataclass
class FunctionResult:
    result: Any
    experiment_case: ExperimentCase

@dataclass
class ExperimentCaseResults:
    main_result: FunctionResult
    variant_results: list[FunctionResult]

@asynccontextmanager
async def _set_experiment_case(experiment_case: ExperimentCase):
    token = current_experiment_case.set(experiment_case)
    try:
        yield
    finally:
        current_experiment_case.reset(token)

class ExperimentRunner:
    def __init__(self, entry_point_fn: ExperimentFunction, await_background_cases: bool = True) -> None:
        self.entry_point_fn: ExperimentFunction = entry_point_fn
        self.await_background_cases: bool = await_background_cases
    
    async def start(self, *args: Any, **kwargs: Any) -> ExperimentCaseResults:
        main_case, variant_cases = self.entry_point_fn.get_experiment_cases()
        async with _set_experiment_case(main_case):
            main = await self.run_with_context(self.entry_point_fn)(*args, **kwargs)

        tasks = []
        for variant_case in variant_cases:
            async with _set_experiment_case(variant_case):
                tasks.append(asyncio.create_task(self.run_with_context(self.entry_point_fn)(*args, **kwargs)))
        
        variants: list[ExperimentCaseResults] = []
        if self.await_background_cases:
            variants = await asyncio.gather(*tasks)

        main_result = main.main_result
        variant_results = [v.main_result for v in variants]
        

        return ExperimentCaseResults(main_result=main_result, variant_results=variant_results)

    
    def run_with_context(self, exp: ExperimentFunction) -> Callable[..., CoroutineType[Any, Any, ExperimentCaseResults]]:
        experiment_case = current_experiment_case.get()
        
        if experiment_case is None:
            raise RuntimeError("No current experiment case set in context.")
        
        async def execute(*args: Any, **kwargs: Any) -> ExperimentCaseResults:
            result = await exp(experiment_case, *args, **kwargs)
            main_result = FunctionResult(result=result, experiment_case=experiment_case)
            return ExperimentCaseResults(main_result=main_result, variant_results=[])
        
        return execute



experiment_runner: ContextVar[ExperimentRunner | None] = ContextVar(
    "spearmint_experiment_runner", default=None
)

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
                async with Spearmint.run(func) as runner:
                    results = await runner(*args, **kwargs)
                    return results.main_result.result

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
    async def run(func: Callable[..., Any], await_background_cases: bool = False):
        """Run the given function as an experiment."""

        experiment_fn = experiment_fn_registry.get_experiment(func)
        
        runner = experiment_runner.get()
        if not runner:
            runner = ExperimentRunner(entry_point_fn=experiment_fn, await_background_cases=await_background_cases)
            token = experiment_runner.set(runner)
            try:
                yield runner.start
            finally:
                experiment_runner.reset(token)
        else:
            yield runner.run_with_context(experiment_fn)


def experiment(
    configs: Sequence[dict[str, Any] | Config | str | Path],
    branch_strategy: Callable[..., tuple[Config, list[Config]]] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for wrapping functions with experiment execution strategy.

    This decorator wraps an async function and orchestrates its execution
    through the provided strategy, handling config injection and logging.

    Args:
        configs: Sequence of configurations for the experiment
        branch_strategy: Strategy instance to use for execution

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
        configs=configs,
        branch_strategy=branch_strategy,
    )
    return spearmint_instance.experiment()
