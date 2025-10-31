"""Spearmint Framework.

A framework for experimentation with LLMs and document processing.
"""

import asyncio
import inspect
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from functools import wraps
from pathlib import Path
from typing import Any, Generic, TypeVar
from uuid import uuid4

import mlflow
from pydantic import BaseModel

from spearmint.config.dynamic_value import generate_configurations
from spearmint.strategies.single_config import SingleConfigStrategy

from .branch import Branch, BranchContainer
from .config.config import Config
from .strategies import Strategy
from .utils.handlers import jsonl_handler, yaml_handler

TModel = TypeVar("TModel", bound=BaseModel, covariant=True)
R = TypeVar("R")

# from .experiment import experiment as experiment_decorator
__version__ = "0.1.0"


class Spearmint:
    """Main Spearmint class for managing experiments and strategies."""

    def __init__(
        self,
        strategy: type[Strategy] | None = None,
        configs: list[dict[str, Any] | Config] | None = None,
        bindings: dict[type[BaseModel], str] | None = None,
        evaluators: Sequence[Callable[..., Any]] | None = None,
    ) -> None:
        self.strategy: type[Strategy] = strategy or SingleConfigStrategy
        self.configs: list[Config] = self._parse_configs(configs or [])
        self.bindings: dict[type[BaseModel], str] = {Config: ""} if bindings is None else bindings
        self.evaluators: list[Callable[..., Any]] = list(evaluators) if evaluators else []
        self._config_handler: Callable[[str | Path], list[dict[str, Any]]] = yaml_handler
        self._dataset_handler: Callable[[str | Path], list[dict[str, Any]]] = jsonl_handler
        self._experiments: dict[str, dict[str, Any]] = defaultdict(dict)
        self._active_line_id: Any = None

    def _parse_configs(self, configs: list[Any]) -> list[Config]:
        """
        Manually set configurations.

        Args:
            *args: Variable number of configuration dictionaries.
        """
        result = []
        for cfg in configs:
            if isinstance(cfg, BaseModel):
                result.append(Config(cfg.model_dump()))
            elif isinstance(cfg, dict):
                result.extend(generate_configurations(cfg))
            elif isinstance(cfg, str) or isinstance(cfg, Path):
                loaded_configs = self._config_handler(cfg)
                result.extend([Config(loaded_cfg) for loaded_cfg in loaded_configs])
        return result

    def experiment(
        self,
        strategy: type[Strategy] | None = None,
        configs: list[dict[str, Any] | Config | str | Path] | None = None,
        bindings: dict[type[BaseModel], str] | None = None,
        evaluators: Sequence[Callable[..., Any]] | None = None,
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
        executor = ThreadPoolExecutor()
        strategy_cls = strategy or self.strategy
        selected_configs = configs or self.configs
        selected_bindings = bindings or self.bindings
        selected_evaluators = evaluators or self.evaluators

        strategy_instance = strategy_cls(
            configs=self._parse_configs(selected_configs),
            bindings=selected_bindings,
        )

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._experiments[func.__name__]["evaluators"] = selected_evaluators
            self._experiments[func.__name__]["config_ids"] = strategy_instance.config_ids

            @wraps(func)
            async def awrapper(*args: Any, **kwargs: Any) -> Any:
                return await strategy_instance.run(
                    func, *args, active_line_id=self._active_line_id, **kwargs
                )

            @wraps(func)
            def swrapper(*args: Any, **kwargs: Any) -> Any:
                result = executor.submit(lambda: asyncio.run(awrapper(*args, **kwargs)))
                r = result.result()
                return r

            return awrapper if inspect.iscoroutinefunction(func) else swrapper

        return decorator

    def run(
        self,
        func: Callable[..., Any],
        dataset: list[dict[str, Any]] | Path | str,
        skip_eval: bool = False,
    ) -> list[dict[str, Any]]:
        """Run a function with the loaded dataset and configurations.

        Args:
            func: The function to run.
            skip_eval: If True, skip evaluation after running the experiment.
        """
        if isinstance(dataset, (str, Path)):
            dataset = self._dataset_handler(dataset)

        for data_line in dataset:
            kwargs = {}
            for param in inspect.signature(func).parameters.keys():
                if param in data_line:
                    kwargs[param] = data_line[param]

            data_line["_id"] = data_line.get("_id", uuid4())
            try:
                self._active_line_id = data_line["_id"]
                if inspect.iscoroutinefunction(func):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.run_until_complete(func(**kwargs))
                    except RuntimeError:
                        asyncio.run(func(**kwargs))
                else:
                    func(**kwargs)
            finally:
                self._active_line_id = None

        results = dataset
        if not skip_eval:
            results = self.evaluate(dataset)

        return results

    def evaluate(self, dataset: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Evaluate all experiments using their registered evaluators."""
        for experiment_info in self._experiments.values():
            evaluators = experiment_info.get("evaluators", [])
            config_ids = experiment_info.get("config_ids", [])
            for line in dataset:
                for config_id in config_ids:
                    trace = self._get_trace(line_id=line["_id"], config_id=config_id)
                    results = {"config_id": config_id}
                    for evaluator in evaluators:
                        results[evaluator.__name__] = evaluator(line["expected"], trace)
                    line["_evaluations"] = results
                    experiment_info.setdefault("evaluations", []).append(results)

        return dataset

    def _get_trace(self, line_id: Any, config_id: str) -> dict[str, Any]:
        """Use the MLFlow traces SDK to find the trace for a given line and config ID."""

        # MLFlow doesn't support custom attributes like config_id or line_id in filter strings
        # So we search all traces and filter manually
        traces = list(mlflow.search_traces())

        # Filter by config_id and line_id manually
        matching_traces = []
        for trace in traces:
            # Check trace data for matching attributes
            trace_dict = trace.to_dict()  # type: ignore[attr-defined]
            # Check in the trace's data or info sections for our custom attributes
            data = trace_dict.get("data", {})
            spans = data.get("spans", [])

            # Look for config_id and line_id in span attributes
            for span in spans:
                attributes = span.get("attributes", {})
                if attributes.get("config_id") == config_id and attributes.get("line_id") == str(
                    line_id
                ):
                    matching_traces.append(trace)
                    break

        if not matching_traces:
            raise ValueError(f"No trace found for line_id={line_id} and config_id={config_id}")
        if len(matching_traces) > 1:
            raise ValueError(
                f"Multiple traces found for line_id={line_id} and config_id={config_id}"
            )

        return dict(matching_traces[0].to_dict())  # type: ignore[attr-defined]


__all__ = ["__version__", "Branch", "BranchContainer", "Spearmint"]
