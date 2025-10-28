"""Spearmint Framework.

A framework for experimentation with LLMs and document processing.
"""

import asyncio
import inspect
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

from .branch import Branch, BranchContainer
from .strategies import Strategy
from .utils.handlers import jsonl_handler, yaml_handler

# from .experiment import experiment as experiment_decorator
__version__ = "0.1.0"


class Spearmint:
    """Main Spearmint class for managing experiments and strategies."""

    def __init__(self) -> None:
        self.strategy: Strategy | None = None
        self.configs: list[dict[str, Any]] = []
        self._config_handler: Callable[[str | Path], list[dict[str, Any]]] = (
            yaml_handler
        )
        self._dataset_handler: Callable[[str | Path], list[dict[str, Any]]] = (
            jsonl_handler
        )
        self._evaluators: list[Callable[..., Any]] = []

    def get_config(self) -> dict[str, Any]:
        """Get the next configuration from the config pool."""
        return {}

    def set_strategy(self, strategy: Strategy) -> None:
        """Set the experiment execution strategy."""
        self.strategy = strategy

    def load_config(self, config_path: str | Path) -> None:
        """
        Load configuration from a YAML file.

        Args:
            config_path: str or Path to the YAML configuration file.
        """
        self.config = self._config_handler(config_path)

    def load_dataset(self, dataset_path: str | Path) -> None:
        """
        Specify a dataset for the hypothesis.

        Args:
            dataset_path: Path to the dataset file.
        """
        self.dataset = self._dataset_handler(dataset_path)

    def experiment(
        self, strategy: Strategy | None = None
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

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def awrapper(*args: Any, **kwargs: Any) -> Any:
                selected_strategy = strategy or self.strategy
                if selected_strategy is None:
                    raise ValueError(
                        "Experiment strategy is not set. Use 'set_strategy' first."
                    )
                return await selected_strategy.run(func, self.configs, *args, **kwargs)

            @wraps(func)
            def swrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    loop = asyncio.get_running_loop()
                    return loop.run_until_complete(awrapper(*args, **kwargs))
                except RuntimeError:
                    return asyncio.run(awrapper(*args, **kwargs))

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

            async def runner():
                # TODO: parallelize options
                for data_line in self.dataset:
                    await func(data_line)

            try:
                loop = asyncio.get_running_loop()
                loop.run_until_complete(runner())
            except RuntimeError:
                asyncio.run(runner())
        else:
            for data_line in self.dataset:
                func(data_line)

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
