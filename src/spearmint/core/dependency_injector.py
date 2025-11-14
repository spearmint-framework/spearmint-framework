import inspect
from collections.abc import Callable
from typing import Any, Union

from pydantic import BaseModel


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
