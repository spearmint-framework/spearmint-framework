"""Experiment execution runtime."""

from __future__ import annotations

import asyncio
import contextvars
import inspect
import logging
import threading
from collections.abc import AsyncIterator, Awaitable, Callable, Coroutine, Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from typing import Any

from .context import current_experiment_case, experiment_runner, set_experiment_case
from .experiment_function import ExperimentCase, ExperimentFunction
from .registry import experiment_fn_registry

logger = logging.getLogger(__name__)


@dataclass
class FunctionResult:
    result: Any
    experiment_case: ExperimentCase


@dataclass
class ExperimentCaseResults:
    main_result: FunctionResult
    variant_results: list[FunctionResult]


def _run_coroutine_sync(coro: Awaitable[Any]) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # When there's no running loop, we can safely use asyncio.run
        # Note: asyncio.run expects a Coroutine, but in practice exp() will
        # return a coroutine when the function is async def.
        return asyncio.run(coro)  # type: ignore[arg-type]

    ctx = contextvars.copy_context()
    with ThreadPoolExecutor(max_workers=1) as executor:
        future: Any = executor.submit(ctx.run, asyncio.run, coro)  # type: ignore[arg-type]
        return future.result()


class ExperimentRunner:
    def __init__(self, entry_point_fn: ExperimentFunction, await_background_cases: bool = True) -> None:
        self.entry_point_fn: ExperimentFunction = entry_point_fn
        self.await_background_cases: bool = await_background_cases

    def _handle_background_task_exception(self, task: asyncio.Task[Any]) -> None:
        """Handle exceptions from background variant tasks."""
        try:
            task.result()
        except asyncio.CancelledError:
            # Task was cancelled, which is a normal control flow mechanism
            pass
        except Exception:
            logger.exception(
                "Exception in background variant task for experiment '%s'",
                self.entry_point_fn.func.__name__,
            )

    def start(self, *args: Any, **kwargs: Any) -> ExperimentCaseResults:
        main_case, variant_cases = self.entry_point_fn.get_experiment_cases()
        with set_experiment_case(main_case):
            main = self.run_with_context(self.entry_point_fn)(*args, **kwargs)

        variant_results: list[FunctionResult] = []
        if variant_cases:
            if self.await_background_cases:
                with ThreadPoolExecutor() as executor:
                    futures = []
                    for variant_case in variant_cases:
                        ctx = contextvars.copy_context()
                        futures.append(
                            executor.submit(
                                ctx.run, self._run_variant_sync, variant_case, *args, **kwargs
                            )
                        )
                    for future in futures:
                        variant_results.append(future.result())
            else:
                for variant_case in variant_cases:
                    ctx = contextvars.copy_context()
                    thread = threading.Thread(
                        target=ctx.run,
                        args=(self._run_variant_sync, variant_case, *args),
                        kwargs=kwargs,
                        daemon=True,
                    )
                    thread.start()

        return ExperimentCaseResults(main_result=main.main_result, variant_results=variant_results)

    async def start_async(self, *args: Any, **kwargs: Any) -> ExperimentCaseResults:
        main_case, variant_cases = self.entry_point_fn.get_experiment_cases()
        with set_experiment_case(main_case):
            main = await self.run_with_context_async(self.entry_point_fn)(*args, **kwargs)

        variant_results: list[FunctionResult] = []
        if variant_cases:
            tasks = [
                asyncio.create_task(self._run_variant_async(variant_case, *args, **kwargs))
                for variant_case in variant_cases
            ]
            if self.await_background_cases:
                variant_results = await asyncio.gather(*tasks)
            else:
                # Add done callbacks to handle exceptions in background tasks
                for task in tasks:
                    task.add_done_callback(self._handle_background_task_exception)

        return ExperimentCaseResults(main_result=main.main_result, variant_results=variant_results)

    def run_with_context(self, exp: ExperimentFunction) -> Callable[..., ExperimentCaseResults]:
        experiment_case = current_experiment_case.get()

        if experiment_case is None:
            raise RuntimeError("No current experiment case set in context.")

        def execute(*args: Any, **kwargs: Any) -> ExperimentCaseResults:
            result = exp(experiment_case, *args, **kwargs)
            if inspect.isawaitable(result):
                result_value = _run_coroutine_sync(result)
            else:
                result_value = result
            main_result = FunctionResult(result=result_value, experiment_case=experiment_case)
            return ExperimentCaseResults(main_result=main_result, variant_results=[])

        return execute

    def run_with_context_async(
        self, exp: ExperimentFunction
    ) -> Callable[..., Coroutine[Any, Any, ExperimentCaseResults]]:
        experiment_case = current_experiment_case.get()

        if experiment_case is None:
            raise RuntimeError("No current experiment case set in context.")

        async def execute(*args: Any, **kwargs: Any) -> ExperimentCaseResults:
            result = exp(experiment_case, *args, **kwargs)
            if inspect.isawaitable(result):
                result_value = await result
            else:
                result_value = result
            main_result = FunctionResult(result=result_value, experiment_case=experiment_case)
            return ExperimentCaseResults(main_result=main_result, variant_results=[])

        return execute

    def _run_variant_sync(
        self, variant_case: ExperimentCase, *args: Any, **kwargs: Any
    ) -> FunctionResult:
        with set_experiment_case(variant_case):
            result = self.run_with_context(self.entry_point_fn)(*args, **kwargs)
            return result.main_result

    async def _run_variant_async(
        self, variant_case: ExperimentCase, *args: Any, **kwargs: Any
    ) -> FunctionResult:
        with set_experiment_case(variant_case):
            result = await self.run_with_context_async(self.entry_point_fn)(*args, **kwargs)
            return result.main_result


@contextmanager
def run_experiment(
    func: Callable[..., Any], await_background_cases: bool = False
) -> Iterator[Callable[..., ExperimentCaseResults]]:
    """Run the given function as a sync experiment."""
    experiment_fn = experiment_fn_registry.get_experiment(func)

    runner = experiment_runner.get()
    if not runner:
        runner = ExperimentRunner(
            entry_point_fn=experiment_fn, await_background_cases=await_background_cases
        )
        token = experiment_runner.set(runner)
        try:
            yield runner.start
        finally:
            experiment_runner.reset(token)
    else:
        yield runner.run_with_context(experiment_fn)


@asynccontextmanager
async def run_experiment_async(
    func: Callable[..., Any], await_background_cases: bool = False
) -> AsyncIterator[Callable[..., Coroutine[Any, Any, ExperimentCaseResults]]]:
    """Run the given function as an async experiment."""
    experiment_fn = experiment_fn_registry.get_experiment(func)

    runner = experiment_runner.get()
    if not runner:
        runner = ExperimentRunner(
            entry_point_fn=experiment_fn, await_background_cases=await_background_cases
        )
        token = experiment_runner.set(runner)
        try:
            yield runner.start_async
        finally:
            experiment_runner.reset(token)
    else:
        yield runner.run_with_context_async(experiment_fn)
