"""Spearmint Framework.

A framework for experimentation with LLMs and document processing.
"""

import asyncio
import inspect
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from functools import wraps
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from spearmint.config.dynamic_value import _generate_configurations
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
        configs: list[dict[str, Any]] | None = None,
        bindings: dict[type[BaseModel], str] | None = None,
    ) -> None:
        if configs is None:
            configs = []
        self.strategy: type[Strategy] = strategy or SingleConfigStrategy
        self.configs: list[dict[str, Any]] = configs or []
        self.bindings: dict[type[BaseModel], str] = {Config: ""} if bindings is None else bindings
        self._config_handler: Callable[[str | Path], list[dict[str, Any]]] = yaml_handler
        self._dataset_handler: Callable[[str | Path], list[dict[str, Any]]] = jsonl_handler
        self._evaluators: list[Callable[..., Any]] = []

    def load_config(self, config_path: str | Path) -> None:
        """
        Load configuration from a YAML file.

        Args:
            config_path: str or Path to the YAML configuration file.
        """
        self.configs = self._config_handler(config_path)

    def add_config(self, *args: Any) -> None:
        """
        Manually set configurations.

        Args:
            *args: Variable number of configuration dictionaries.
        """
        for cfg in args:
            if isinstance(cfg, BaseModel):
                self.configs.append(cfg.model_dump())
            elif isinstance(cfg, dict):
                self.configs.extend(_generate_configurations(cfg))
            elif isinstance(cfg, str) or isinstance(cfg, Path):
                loaded_configs = self._config_handler(cfg)
                self.configs.extend(loaded_configs)

    def load_dataset(self, dataset_path: str | Path) -> None:
        """
        Specify a dataset for the hypothesis.

        Args:
            dataset_path: Path to the dataset file.
        """
        self.dataset = self._dataset_handler(dataset_path)

    def experiment(
        self,
        strategy: type[Strategy] | None = None,
        configs: list[dict[str, Any]] | None = None,
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


        def inject_model(model_cls: type[TModel]) -> Callable[[Callable[[str, TModel, int | None], R]], Callable[[str, int | None], R]]:
            def decorator(fn: Callable[[str, TModel, int | None], R]) -> Callable[[str, int | None], R]:
                def wrapper(text: str, max_length: int | None = 150) -> R:
                    model_cfg = resolve_model(model_cls)  # implement this
                    return fn(text, model_cfg, max_length)
                return wrapper
            return decorator
        """
        executor = ThreadPoolExecutor()

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def awrapper(*args: Any, **kwargs: Any) -> Any:
                strategy_cls = strategy or self.strategy
                selected_configs = configs or self.configs
                selected_bindings = bindings or self.bindings

                strategy_instance = strategy_cls(
                    configs=selected_configs,
                    bindings=selected_bindings,
                )

                return await strategy_instance.run(func, *args, **kwargs)

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
        skip_eval: bool = False,
    ) -> None:
        """Run a function with the loaded dataset and configurations.

        Args:
            func: The function to run.
            skip_eval: If True, skip evaluation after running the experiment.
        """
        if not self.dataset:
            raise ValueError("Dataset not loaded. Use 'load_dataset' first.")

        if not self.configs:
            raise ValueError("Config not loaded. Use 'load_config' first.")

        if inspect.iscoroutinefunction(func):

            async def runner() -> None:
                # TODO: parallelize options
                for data_line in self.dataset:
                    kwargs = {}
                    for param in inspect.signature(func).parameters.keys():
                        if param in data_line:
                            kwargs[param] = data_line[param]
                    await func(**kwargs)

            try:
                loop = asyncio.get_running_loop()
                loop.run_until_complete(runner())
            except RuntimeError:
                asyncio.run(runner())
        else:
            for data_line in self.dataset:
                kwargs = {}
                for param in inspect.signature(func).parameters.keys():
                    if param in data_line:
                        kwargs[param] = data_line[param]
                func(**kwargs)

        if not skip_eval:
            for evaluator in self._evaluators:
                evaluator(self.dataset)

    # def REVIEW_THIS():
    #     if experiment_name not in self._experiments:
    #         raise ValueError(f"Experiment '{experiment_name}' not found in hypothesis")
    #     experiment = self._experiments[experiment_name]
    #     experiment_variants = []
    #     for config in _generate_configurations(config):
    #         # print(f"Running experiment with configuration: {config}")
    #         variant_dataset = copy.deepcopy(self.dataset)
    #         for line in variant_dataset:
    #             experiment_inputs = self._inputs.copy()
    #             for key, value in self._inputs.items():
    #                 experiment_inputs[key] = line.get(value)

    #             # inspect the experiment signature to ensure all inputs are provided
    #             full_arg_spec = inspect.getfullargspec(experiment._run_fn)
    #             # print(full_arg_spec)
    #             experiment_args = []
    #             for arg in full_arg_spec.args:
    #                 if arg in experiment_inputs:
    #                     experiment_args.append(experiment_inputs.pop(arg))
    #                 else:
    #                     raise ValueError(
    #                         f"Missing required input '{arg}' for experiment '{experiment_name}'"
    #                     )

    #             # print(f"Running experiment with args: {experiment_args} and config: {config}")
    #             line["response"] = await experiment(*experiment_args, **config)

    #         # Run the experiment with the provided configuration
    #         experiment_variants.append({"config": config, "dataset": variant_dataset})

    #     # Run all experiment variants concurrently
    #     # parallel_tasks = []
    #     # for variant in experiment_variants:
    #     #     for line in variant["dataset"]:
    #     #         parallel_tasks.append(line["response"])

    #     # await asyncio.gather(*parallel_tasks, return_exceptions=True)

    #     for variant in experiment_variants:
    #         for line in variant["dataset"]:
    #             # Evaluate the response using all evaluators
    #             for evaluator in self._evaluators:
    #                 line[evaluator.__class__.__name__] = evaluator(**line)


__all__ = ["__version__", "Branch", "BranchContainer", "Spearmint"]
