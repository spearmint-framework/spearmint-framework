"""
Hypothesis module for the Spearmint framework.

This module contains the Hypothesis class, which is the main entrypoint for creating
and running experiments with the Spearmint framework.
"""

import copy
import inspect
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Type, TypeVar

from .config import _generate_configurations
from .experiment import Experiment

# Import the Experiment type for type hints
if TYPE_CHECKING:
    from .experiment import Experiment

F = TypeVar("F", bound=Callable[..., Any])


class OfflineHypothesis:
    """
    Hypothesis is the main class for creating and running experiments.

    It provides methods for configuring experiments, adding services, and
    running experiments with specific configurations.
    """

    def __init__(self, name: str) -> None:
        """Initialize a new Hypothesis instance."""
        self._experiments = {}
        self._configurables = {}
        self._services = []
        self._evaluators = []
        self._dataset_handler = jsonl_handler
        self.dataset = []
        self._config_handler = yaml_handler
        self.config = {}
        self._inputs = {}

    def configure(self, config_path: str) -> None:
        """
        Load configuration from a YAML file.

        Args:
            config_path: Path to the YAML configuration file.
        """
        self.config = self._config_handler(config_path)

    def load_dataset(self, dataset_path: str) -> None:
        """
        Specify a dataset for the hypothesis.

        Args:
            dataset_path: Path to the dataset file.
        """
        self.dataset = self._dataset_handler(dataset_path)

    def inputs(self, inputs: Dict[str, Any]) -> None:
        """
        Specify inputs for the hypothesis.

        Args:
            inputs: A dictionary of inputs to use in the experiments.
        """
        if not isinstance(inputs, dict):
            raise TypeError("Expected a dictionary for inputs")
        self._inputs = inputs

    def add_service(self, service_class: Type[Any]) -> None:
        """
        Add a service to the hypothesis.

        Args:
            service_class: The service class to add.
        """
        if not inspect.isclass(service_class):
            raise TypeError(
                f"Expected a class for service. Got {type(service_class).__name__} ({service_class})"
            )

        self._services.append(service_class)

    def add_evaluator(self, evaluator: Callable[..., Any]) -> None:
        """
        Add an evaluator to the hypothesis.

        Args:
            evaluator: The evaluator function to add.
        """
        if not callable(evaluator):
            raise TypeError(
                f"Expected a callable for evaluator. Got {type(evaluator).__name__} ({evaluator})"
            )
        self._evaluators.append(evaluator)

    def add_experiment(self, experiment: Experiment, name: str) -> None:
        """
        Add an experiment to the hypothesis with a specific name.

        Args:
            experiment: The experiment to add.
            name: The name to give the experiment.
        """
        if not isinstance(experiment, Experiment):
            raise TypeError("Expected an instance of Experiment")
        self._experiments[name] = experiment

    def add_configurable(self, fn: Callable, name: str) -> None:
        """
        Add an experiment to the hypothesis with a specific name.

        Args:
            experiment: The experiment to add.
            name: The name to give the experiment.
        """
        self._configurables[name] = fn

    def experiment_fn_decorator(self, name: Optional[str] = None) -> Callable[..., Any]:
        """
        Add an experiment function to the hypothesis.

        Args:
            experiment_fn: The function that defines the experiment.
            name: Optional name for the experiment. If not provided, the function's name will be used.

        Returns:
            The original function (to support decorator usage).
        """

        def decorator(experiment_fn: F) -> Callable[..., Any]:
            """
            Decorator to add an experiment function to the hypothesis.

            Args:
                experiment_fn: The function that defines the experiment.
                name: Optional name for the experiment. If not provided, the function's name will be used.

            Returns:
                The original function (to support decorator usage).
            """
            if not callable(experiment_fn):
                raise TypeError(
                    f"Expected a callable for experiment_fn. Got {type(experiment_fn).__name__} ({experiment_fn})"
                )

            local_name = name
            if local_name is None:
                local_name = experiment_fn.__name__

            self.add_experiment(Experiment(experiment_fn), local_name)

        return decorator

    def configurable_fn_decorator(
        self, name: Optional[str] = None
    ) -> Callable[..., Any]:
        """
        Add an configurable function to the hypothesis.

        Args:
            configurable_fn: The function that defines the configurable.
            name: Optional name for the configurable. If not provided, the function's name will be used.

        Returns:
            The original function (to support decorator usage).
        """
        print("init configurable_fn_decorator")
        print(f"name: {name}")

        def decorator(configurable_fn: F) -> Callable[..., Any]:
            """
            Decorator to add an configurable function to the hypothesis.

            Args:
                configurable_fn: The function that defines the configurable.
                name: Optional name for the configurable. If not provided, the function's name will be used.

            Returns:
                The original function (to support decorator usage).
            """
            print("running decorator")
            if not callable(configurable_fn):
                raise TypeError(
                    f"Expected a callable for configurable_fn. Got {type(configurable_fn).__name__} ({configurable_fn})"
                )

            # Create a new function with the same arg signature, but no kwargs that wraps the original function with the configuration
            # this allows IDEs to show the signature without the configuration
            def wrapped_fn(*args: Any, **kwargs: Any) -> Any:
                """
                Wrapped function that calls the original configurable function with the provided arguments and configuration.

                Args:
                    *args: Positional arguments to pass to the configurable function.
                    **kwargs: Keyword arguments to pass to the configurable function.

                Returns:
                    The result of calling the configurable function.
                """
                local_name = name
                if local_name is None:
                    local_name = configurable_fn.__name__
                config_inputs = self.config.get(local_name, {})
                fn_kwargs = {}
                full_arg_spec = inspect.getfullargspec(configurable_fn)
                for kwarg in full_arg_spec.kwonlyargs:
                    if kwarg in config_inputs:
                        fn_kwargs[kwarg] = config_inputs.get(kwarg)

                # Merge the configuration into kwargs
                merged_kwargs = {**fn_kwargs, **kwargs}
                print(
                    f"Running {configurable_fn.__name__} with args: {args} and kwargs: {merged_kwargs}"
                )
                result = configurable_fn(*args, **merged_kwargs)
                return result

            # Set the name of the wrapped function to the original function's name
            # wrapped_fn.__name__ = configurable_fn.__name__
            # wrapped_fn.__doc__ = configurable_fn.__doc__

            # update the arg spec of the wrapped function to match the original function
            # wrapped_fn.__signature__ = inspect.signature(configurable_fn)

            return wrapped_fn

        return decorator

    async def run(self, experiment_name: str, config: Dict[str, Any]) -> Any:
        """
        Run an experiment with an optional configuration.

        Args:
            experiment: The experiment to run.
            config: Optional configuration to use when running the experiment.

        Returns:
            The result of running the experiment.
        """
        if experiment_name not in self._experiments:
            raise ValueError(f"Experiment '{experiment_name}' not found in hypothesis")
        experiment = self._experiments[experiment_name]
        experiment_variants = []
        for config in _generate_configurations(config):
            # print(f"Running experiment with configuration: {config}")
            variant_dataset = copy.deepcopy(self.dataset)
            for line in variant_dataset:
                experiment_inputs = self._inputs.copy()
                for key, value in self._inputs.items():
                    experiment_inputs[key] = line.get(value)

                # inspect the experiment signature to ensure all inputs are provided
                full_arg_spec = inspect.getfullargspec(experiment._run_fn)
                print(full_arg_spec)
                experiment_args = []
                for arg in full_arg_spec.args:
                    if arg in experiment_inputs:
                        experiment_args.append(experiment_inputs.pop(arg))
                    else:
                        raise ValueError(
                            f"Missing required input '{arg}' for experiment '{experiment_name}'"
                        )

                fn_kwargs = {}
                for kwarg in full_arg_spec.kwonlyargs:
                    if kwarg in config:
                        fn_kwargs[kwarg] = config.get(kwarg)

                # print(f"Running experiment with args: {experiment_args} and config: {config}")
                print(
                    f"Running experiment {experiment_name} with args: {experiment_args} and config: {fn_kwargs}"
                )
                line["response"] = await experiment(*experiment_args, **fn_kwargs)
                print("after run")
            # Run the experiment with the provided configuration
            experiment_variants.append({"config": config, "dataset": variant_dataset})

        # Run all experiment variants concurrently
        # parallel_tasks = []
        # for variant in experiment_variants:
        #     for line in variant["dataset"]:
        #         parallel_tasks.append(line["response"])

        # await asyncio.gather(*parallel_tasks, return_exceptions=True)

        for variant in experiment_variants:
            for line in variant["dataset"]:
                # Evaluate the response using all evaluators
                for evaluator in self._evaluators:
                    line[evaluator.__class__.__name__] = evaluator(**line)

        return experiment_variants


def jsonl_handler(file_path: str) -> List[Dict[str, Any]]:
    """
    Handler for reading JSON Lines files.

    Args:
        file_path: Path to the JSON Lines file.

    Returns:
        A list of dictionaries representing the JSON Lines data.
    """
    import json

    with open(file_path, "r") as f:
        return [json.loads(line) for line in f]


def yaml_handler(file_path: str) -> Dict[str, Any]:
    """
    Handler for reading YAML files.

    Args:
        file_path: Path to the YAML file.

    Returns:
        A dictionary representing the YAML data.
    """
    import yaml

    with open(file_path, "r") as f:
        return yaml.safe_load(f)
