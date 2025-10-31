"""Base strategy protocol and branch execution helper (generic).

Defines the generic `Strategy` Protocol that all execution strategies
must implement, along with the internal `_execute_branch` helper used by
concrete strategies to perform a single branch execution and logging lifecycle.

The generic type parameter `TModel` is bound to `pydantic.BaseModel` so that
strategies operate on validated configuration models rather than raw
``dict`` objects. This improves type-safety and enables IDE assistance.
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Sequence
from copy import deepcopy
from typing import Any, Union

import mlflow
from pydantic import BaseModel

from ..branch import Branch
from ..config import Config


class Strategy(ABC):
    """Abstract base class for execution strategies."""

    def __init__(self, configs: Sequence[Config], bindings: dict[type[BaseModel], str]) -> None:
        """Initialize the strategy instance."""
        self.configs = configs
        self.bindings = bindings

    @property
    def config_ids(self) -> list[str]:
        """Get list of config IDs for all configs."""
        return [cfg["config_id"] for cfg in self.configs]

    @abstractmethod
    async def run(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:  # pragma: no cover - protocol definition only
        """Execute the experiment function with the given configs.

        Args:
            func: Async function to execute (should accept config kwarg)
            configs: Sequence of configuration model instances
            *args: Positional arguments to pass to func
            **kwargs: Keyword arguments to pass to func

        Returns:
            Strategy-specific return value (direct result, BranchContainer, etc.)
        """
        ...

    def _bind_config(self, config: Config) -> list[BaseModel]:
        """Bind configs to model classes based on provided bindings.

        This method can be used to map configuration model instances
        to function parameters based on type annotations or explicit
        bindings.
        """
        bound_configs = []

        for model_cls, bind_path in self.bindings.items():
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

    async def _execute_branch(
        self,
        func: Callable[..., Awaitable[Any]],
        config: list[BaseModel],
        config_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> Branch:
        """Execute function with a single config and return a Branch with results.

        This helper manages the full branch lifecycle: creation, execution,
        logging, and status tracking.

        Args:
            func: Async function to execute
            config: Configuration dictionary for this execution
            config_id: Unique identifier for this config
            logger: Optional logger backend
            *args: Positional arguments to pass to func
            **kwargs: Keyword arguments to pass to func

        Returns:
            Branch instance with execution results
        """
        # Extract active_line_id for MLFlow tracing
        active_line_id = kwargs.pop("active_line_id", None)

        # Normalize config for Branch storage (store original model instance)
        branch = Branch.start(config_id, config)
        print(f"Starting branch {config_id}")

        # Set up MLFlow trace attributes
        trace_attributes = {"config_id": config_id}
        if active_line_id is not None:
            trace_attributes["line_id"] = active_line_id

        func = mlflow.trace(func, span_type="experiment_branch", attributes=trace_attributes)

        inspect_signature = inspect.signature(func)
        remaining_configs = list(config)
        for param in inspect_signature.parameters.values():
            # Inject config if annotation matches config model class or uses a generic name like 'config'
            for subconfig in remaining_configs[:]:
                if any(
                    issubclass(param_cls, subconfig.__class__)
                    for param_cls in self._resolve_class_types(param.annotation)
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
        try:
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            branch.mark_success(result)

        except Exception as exc:  # noqa: BLE001 - broad to capture and store exception
            branch.mark_failure(exc)

        return branch

    def _resolve_class_types(self, obj: Any) -> list[type]:
        if obj.__class__ == Union:
            return list(obj.__args__)

        if inspect.isclass(obj):
            return [obj]

        return [obj.__class__]


__all__ = ["Strategy"]
