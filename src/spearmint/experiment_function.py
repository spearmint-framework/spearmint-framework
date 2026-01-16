from collections.abc import Callable
from copy import deepcopy
import textwrap
from typing import Annotated, Any, Union, get_args, get_origin, get_type_hints
import inspect
from itertools import product


from matplotlib.text import Annotation
from pydantic import BaseModel

from .configuration import Config, Bind


class ExperimentCase:
    def __init__(self, func_name, config: Config) -> None:
        self.config_map: dict[str, str] = {
            func_name: config["config_id"]
        }
        self._configs: dict[str, Config] = {
            config["config_id"]: config
        }

    def add(self, func_name: str, config: Config) -> None:
        self.config_map[func_name] = config["config_id"]
        self._configs[config["config_id"]] = config

    def get_config_id(self, func_name: str) -> str:
        config_id = self.config_map.get(func_name)
        if config_id is None:
            raise ValueError(f"No config found for function '{func_name}'")
        return config_id


def default_config_handler(configs: list[Config]) -> tuple[Config, list[Config]]:
    if not configs:
        configs = [Config(root={"config_id": "default"})]
    return configs[0], configs[1:]


class ExperimentFunction:
    def __init__(
        self,
        func: Callable[..., Any],
        configs: list[Config] = [],
        config_handler: Callable[..., tuple[Config, list[Config]]] | None = None,
    ) -> None:
        self.func = func
        self.name = func.__qualname__
        self.short_name = func.__name__
        self.config_handler = config_handler or default_config_handler
        self.registered_configs = configs
        self.param_bindings = self._param_bindings()
        self.assigned_configs = self.bind_configs()
        self.inner_calls: dict[str, ExperimentFunction | None] = self._inner_calls()

    async def __call__(self, experiment_case: ExperimentCase, *args: Any, **kwargs: Any) -> Any:
        config_id = experiment_case.get_config_id(self.name)
        assigned_configs = self.assigned_configs.get(config_id, [])
        injected_args, injected_kwargs = self.inject_config(
            self.func, assigned_configs, *args, **kwargs
        )

        return await self.func(*injected_args, **injected_kwargs)

    def get_registered_configs(self) -> tuple[Config, list[Config]]:
        return self.config_handler(self.registered_configs)

    def update_inner_calls(self, experiment: "ExperimentFunction") -> None:
        # Update inner calls if the experiment function matches
        # The AST parsing only gets function names, so we match on short_name
        if experiment.short_name in self.inner_calls:
            self.inner_calls[experiment.short_name] = experiment

    def get_experiment_cases(self) -> tuple[ExperimentCase, list[ExperimentCase]]:
        """
        Get all config paths for this experiment function.
        Returns a tuple containing the main ExperimentCase and a list of
        alternative ExperimentCases.
        
        """

        def collect_options(exp: "ExperimentFunction") -> dict[str, list[Config]]:
            main_config, background_configs = exp.get_registered_configs()
            options: dict[str, list[Config]] = {
                exp.name: [main_config, *background_configs]
            }
            for inner in exp.inner_calls.values():
                if inner is not None:
                    options.update(collect_options(inner))
            return options

        options_by_func = collect_options(self)
        func_names = list(options_by_func.keys())
        option_lists = [options_by_func[name] for name in func_names]

        all_cases: list[ExperimentCase] = []
        for combo in product(*option_lists):
            case = ExperimentCase(func_names[0], combo[0])
            for func_name, config in zip(func_names[1:], combo[1:]):
                case.add(func_name, config)
            all_cases.append(case)

        if not all_cases:
            raise ValueError("No configurations provided for main handler.")

        return all_cases[0], all_cases[1:]

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
    
    def _param_bindings(self) -> dict[str, dict[type[BaseModel], str]]:
        """Bind configs to model classes based on provided bindings.

        This method can be used to map configuration model instances
        to function parameters based on type annotations or explicit
        bindings.
        """
        def get_bindings(ann: Any) -> dict[type[BaseModel], str]:
            bindings: dict[type[BaseModel], str] = {}
            model_cls, *meta = get_args(ann)
            for item in meta:
                if isinstance(item, Bind):
                    bindings[model_cls] = item.path
            return bindings
        
        annotations = get_type_hints(self.func, include_extras=True)

        param_bindings: dict[str, dict[type[BaseModel], str]] = {}
        for param_name, ann in annotations.items():
            if param_name == "return":
                continue
            if get_origin(ann) is Annotated:
                bindings = get_bindings(ann)
                if bindings:
                    param_bindings[param_name] = bindings
            if ann in (BaseModel, Config):
                # Direct type annotation without Annotated
                param_bindings[param_name] = {ann: ""}

        return param_bindings
            
    def bind_configs(self) -> dict[str, list[BaseModel]]:
        """Bind configs to model classes based on provided bindings.

        This method can be used to map configuration model instances
        to function parameters based on type annotations or explicit
        bindings.
        """
        bound_configs_by_id: dict[str, list[BaseModel]] = {}
        for config in self.registered_configs:
            bound_configs_by_id[config["config_id"]] = self.bind_config(config)

        return bound_configs_by_id
    
    def bind_config(self, config: Config) -> list[BaseModel]:
        bound_configs = []

        for param_bind in self.param_bindings.values():
            for model_cls, bind_path in param_bind.items(): 
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



    def inject_config(self,
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
            bound_config= self.param_bindings.get(param.name, {})

            for subconfig in remaining_configs[:]:
                # if any(
                #     issubclass(param_cls, subconfig.__class__)
                #     for param_cls in _resolve_class_types(param.annotation)
                # ):
                if subconfig.__class__ in bound_config:
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



class ExperimentFunctionRegistry:
    
    def __init__(self) -> None:
        self.experiment_fns: dict[str, ExperimentFunction] = {}

    def register_experiment(
            self,
            experiment: ExperimentFunction,
        ) -> None:
        self.experiment_fns[experiment.name] = experiment
        for registered_experiment in self.experiment_fns.values():
            registered_experiment.update_inner_calls(experiment)
            experiment.update_inner_calls(registered_experiment)
    
    def get_experiment(self, func: Callable[..., Any]) -> ExperimentFunction:
        """Get the ExperimentFunction for a given function."""
        experiment = self.experiment_fns.get(func.__qualname__)
        if not experiment:
            raise ValueError(f"No experiment found for function '{func.__qualname__}'")
        return experiment
