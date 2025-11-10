import inspect

from typing import Any, Callable, Union
from pydantic import BaseModel


def inject_config(func: Callable[..., Any], config: list[BaseModel], *args: Any, **kwargs: Any) -> tuple[tuple[Any, ...], dict[str, Any]]:
    inspect_signature = inspect.signature(func)
    remaining_configs = list(config)
    for param in inspect_signature.parameters.values():
        # Inject config if annotation matches config model class or uses a generic name like 'config'
        for subconfig in remaining_configs[:]:
            if any(
                issubclass(param_cls, subconfig.__class__)
                for param_cls in _resolve_class_types(param.annotation)
            ):
                if param.kind in (param.POSITIONAL_ONLY,):
                    args = args + (subconfig,)
                elif (
                    param.kind in (param.KEYWORD_ONLY, param.POSITIONAL_OR_KEYWORD)
                    and param.name not in kwargs
                ):
                    kwargs[param.name] = subconfig
                remaining_configs.remove(subconfig)  # Actually remove from the list
                break

    return args, kwargs


def _resolve_class_types(obj: Any) -> list[type]:
    if obj.__class__ == Union:
        return list(obj.__args__)

    if inspect.isclass(obj):
        return [obj]

    return [obj.__class__]