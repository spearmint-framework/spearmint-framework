"""Base strategy protocol and branch execution helper (generic).

Defines the generic `Strategy[TModel]` Protocol that all execution strategies
must implement, along with the internal `_execute_branch` helper used by
concrete strategies to perform a single branch execution and logging lifecycle.

The generic type parameter `TModel` is bound to `pydantic.BaseModel` so that
strategies operate on validated configuration models rather than raw
``dict`` objects. This improves type-safety and enables IDE assistance.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Sequence
from typing import Any, Generic, Protocol, TypeVar

import mlflow
from pydantic import BaseModel

from ..branch import Branch

TModel = TypeVar("TModel", bound=BaseModel)


class Strategy(Protocol, Generic[TModel]):
    """Protocol defining the interface for experiment execution strategies.

    Implementations receive a sequence of validated configuration model
    instances (``Sequence[TModel]``) instead of raw dicts.
    """

    async def run(
        self,
        func: Callable[..., Awaitable[Any]],
        configs: Sequence[TModel],
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


async def _execute_branch(
    func: Callable[..., Awaitable[Any]],
    config: Sequence[TModel],
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
    # Normalize config for Branch storage (store original model instance)
    branch = Branch.start(config_id, config)
    print(f"Starting branch {config_id}")

    func = mlflow.trace(func, span_type="experiment_branch", attributes={"config_id": config_id})

    inspect_signature = inspect.signature(func)
    for param in inspect_signature.parameters.values():
        # Inject config if annotation matches config model class or uses a generic name like 'config'
        for subconfig in config:
            if issubclass(param.annotation, subconfig.__class__):
                if param.kind in (param.POSITIONAL_ONLY,):
                    args = args + (subconfig,)
                elif (
                    param.kind in (param.KEYWORD_ONLY, param.POSITIONAL_OR_KEYWORD)
                    and param.name not in kwargs
                ):
                    kwargs[param.name] = subconfig
                del subconfig

    try:
        if inspect.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
        branch.mark_success(result)

    except Exception as exc:  # noqa: BLE001 - broad to capture and store exception
        branch.mark_failure(exc)

    return branch


__all__ = ["Strategy", "_execute_branch", "TModel"]
