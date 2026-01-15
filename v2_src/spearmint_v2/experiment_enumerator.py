from collections.abc import Callable
from copy import deepcopy
import textwrap
from typing import Any, Union
import inspect

from pydantic import BaseModel

from .configuration import Config


class ConfigPath:
    def __init__(self, func_name, config: Config) -> None:
        self.configs: dict[str, Config] = {
            func_name: config
        }
        # TODO: move this to where bindings should live
        self.bound_configs: dict[str, list[BaseModel]] = {
            func_name: self._bind_config(config, {Config: ""})
        }

    def add(self, func_name: str, config: Config) -> None:
        self.configs[func_name] = config

    def merge(self, other: "ConfigPath") -> "ConfigPath":
        self.configs.update(other.configs)
        return self
    
    def _bind_config(self, config: Config, bindings: dict[type[BaseModel], str]) -> list[BaseModel]:
        """Bind configs to model classes based on provided bindings.

        This method can be used to map configuration model instances
        to function parameters based on type annotations or explicit
        bindings.
        """
        bound_configs = []

        for model_cls, bind_path in bindings.items():
            # For RootModel, model_dump() returns the root dict
            config_dict = config.model_dump() if hasattr(config, "model_dump") else config.root
            config_data = deepcopy(config_dict)
            parts = bind_path.split(".")
            for part in parts:
                if not part:
                    continue
                if part in config_data:
                    config_data = config_data[part]
                else:
                    raise ValueError(f"Key '{part}' not found in bind path '{bind_path}'")

            bound_configs.append(model_cls.model_validate(config_data))

        return bound_configs


def default_config_handler(configs: list[Config]) -> tuple[Config, list[Config]]:
    if not configs:
        raise ValueError("No configurations provided for main handler.")
    return configs[0], configs[1:]


class Experiment:
    def __init__(
        self,
        func: Callable[..., Any],
        configs: list[Any] = [],
        config_handler: Callable[..., Any] | None = None,
        background_handler: Callable[..., Any] | None = None,
    ) -> None:
        self.func = func
        self.func_name = func.__qualname__
        self.config_handler = config_handler or default_config_handler
        self.configs = configs
        self.inner_calls: dict[str, Experiment | None] = self._inner_calls()

    def update_inner_calls(self, experiment: "Experiment") -> None:
        if experiment.func.__name__ in self.inner_calls:
            self.inner_calls[experiment.func.__name__] = experiment

    def get_config_paths(self) -> tuple[ConfigPath, list[ConfigPath]]:
        """Get all config paths for this experiment function."""
        from itertools import product

        def collect_options(exp: "Experiment") -> dict[str, list[Config]]:
            main_config, background_configs = exp.config_handler(exp.configs)
            options: dict[str, list[Config]] = {
                exp.func_name: [main_config, *background_configs]
            }
            for inner in exp.inner_calls.values():
                if inner is not None:
                    options.update(collect_options(inner))
            return options

        options_by_func = collect_options(self)
        func_names = list(options_by_func.keys())
        option_lists = [options_by_func[name] for name in func_names]

        all_paths: list[ConfigPath] = []
        for combo in product(*option_lists):
            path = ConfigPath(func_names[0], combo[0])
            for func_name, config in zip(func_names[1:], combo[1:]):
                path.add(func_name, config)
            all_paths.append(path)

        if not all_paths:
            raise ValueError("No configurations provided for main handler.")

        return all_paths[0], all_paths[1:]

    def _inner_calls(self) -> dict[str, Any]:
        # Get the functions called within the experiment function
        import ast
        import inspect

        source = textwrap.dedent(inspect.getsource(self.func))
        tree = ast.parse(source)
        inner_calls: dict[str, Any] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                inner_calls[node.func.id] = None
        return inner_calls


def inject_config(
    func: Callable[..., Any], configs: list[BaseModel], *args: Any, **kwargs: Any
) -> tuple[tuple[Any, ...], dict[str, Any]]:
    inspect_signature = inspect.signature(func)
    remaining_configs = list(configs)

    # Track which parameters have been filled by positional arguments
    params_list = list(inspect_signature.parameters.values())
    filled_params = set()

    if not params_list:
        return args, kwargs

    if params_list[0].kind != inspect.Parameter.VAR_POSITIONAL:
        # Mark parameters that are already filled by positional args
        for i, arg in enumerate(args):
            if i < len(params_list):
                param = params_list[i]
                # Only mark as filled if it's not VAR_POSITIONAL (*args)
                if param.kind == inspect.Parameter.VAR_KEYWORD:
                    break

                filled_params.add(param.name)

    # Also mark any kwargs that were explicitly provided
    filled_params.update(kwargs.keys())

    for param in params_list:
        # Skip if parameter is already filled
        if param.name in filled_params:
            continue

        # Skip VAR_POSITIONAL (*args) and VAR_KEYWORD (**kwargs)
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue

        # Inject config if annotation matches config model class
        for subconfig in remaining_configs[:]:
            if any(
                issubclass(param_cls, subconfig.__class__)
                for param_cls in _resolve_class_types(param.annotation)
            ):
                if param.kind in (param.POSITIONAL_ONLY,):
                    args = args + (subconfig,)
                elif param.kind in (param.KEYWORD_ONLY, param.POSITIONAL_OR_KEYWORD):
                    kwargs[param.name] = subconfig
                remaining_configs.remove(subconfig)
                break

    return args, kwargs


def _resolve_class_types(obj: Any) -> list[type]:
    if obj.__class__ == Union:
        return list(obj.__args__)

    if inspect.isclass(obj):
        return [obj]

    return [obj.__class__]



class ExperimentEnumerator:
    
    def __init__(self) -> None:
        self.experiment_fns: dict[str, Experiment] = {}

    def register_experiment(
            self,
            experiment: Experiment,
        ) -> None:
        self.experiment_fns[experiment.func_name] = experiment
        for registered_experiment in self.experiment_fns.values():
            registered_experiment.update_inner_calls(experiment)


    def get_config_paths(self, func: Callable[..., Any]) -> tuple[ConfigPath, list[ConfigPath]]:
        """Get all config paths for a given experiment function."""
        experiment = self.experiment_fns.get(func.__qualname__)
        if not experiment:
            raise ValueError(f"No experiment found for function '{func.__qualname__}'")
        return experiment.get_config_paths()