"""Experiment execution runtime."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from types import CoroutineType
from typing import Any, AsyncIterator, Callable

from .context import current_experiment_case, experiment_runner, set_experiment_case
from .experiment_function import ExperimentCase, ExperimentFunction
from .registry import experiment_fn_registry


@dataclass
class FunctionResult:
    result: Any
    experiment_case: ExperimentCase


@dataclass
class ExperimentCaseResults:
    main_result: FunctionResult
    variant_results: list[FunctionResult]


class ExperimentRunner:
    def __init__(self, entry_point_fn: ExperimentFunction, await_background_cases: bool = True) -> None:
        self.entry_point_fn: ExperimentFunction = entry_point_fn
        self.await_background_cases: bool = await_background_cases

    async def start(self, *args: Any, **kwargs: Any) -> ExperimentCaseResults:
        main_case, variant_cases = self.entry_point_fn.get_experiment_cases()
        async with set_experiment_case(main_case):
            main = await self.run_with_context(self.entry_point_fn)(*args, **kwargs)

        tasks: list[asyncio.Task[ExperimentCaseResults]] = []
        for variant_case in variant_cases:
            async with set_experiment_case(variant_case):
                tasks.append(
                    asyncio.create_task(self.run_with_context(self.entry_point_fn)(*args, **kwargs))
                )

        variants: list[ExperimentCaseResults] = []
        if self.await_background_cases:
            variants = await asyncio.gather(*tasks)

        main_result = main.main_result
        variant_results = [v.main_result for v in variants]

        return ExperimentCaseResults(main_result=main_result, variant_results=variant_results)

    def run_with_context(
        self, exp: ExperimentFunction
    ) -> Callable[..., CoroutineType[Any, Any, ExperimentCaseResults]]:
        experiment_case = current_experiment_case.get()

        if experiment_case is None:
            raise RuntimeError("No current experiment case set in context.")

        async def execute(*args: Any, **kwargs: Any) -> ExperimentCaseResults:
            result = await exp(experiment_case, *args, **kwargs)
            main_result = FunctionResult(result=result, experiment_case=experiment_case)
            return ExperimentCaseResults(main_result=main_result, variant_results=[])

        return execute


@asynccontextmanager
async def run_experiment(
    func: Callable[..., Any], await_background_cases: bool = False
) -> AsyncIterator[Callable[..., CoroutineType[Any, Any, ExperimentCaseResults]]]:
    """Run the given function as an experiment."""

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