"""Context variables for Spearmint execution."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, Iterator


if TYPE_CHECKING:
    from .experiment_function import ExperimentCase
    from .runner import ExperimentRunner


current_experiment_case: ContextVar[ExperimentCase | None] = ContextVar(
    "spearmint_experiment_case", default=None
)

experiment_runner: ContextVar["ExperimentRunner | None"] = ContextVar(
    "spearmint_experiment_runner", default=None
)

_runtime_context: ContextVar[RuntimeContext | None] = ContextVar(
    "spearmint_runtime_context", default=None
)


@contextmanager
def set_experiment_case(experiment_case: ExperimentCase) -> Iterator[None]:
    token = current_experiment_case.set(experiment_case)
    try:
        yield
    finally:
        current_experiment_case.reset(token)


class RuntimeContext:
    """Context manager for setting runtime context variables."""

    def __init__(self) -> None:
        self.context = {}

    def set(self, key: str, value: Any) -> None:
        self.context[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.context.get(key, default)


@contextmanager
def runtime_context() -> Iterator[RuntimeContext]:
    """Context manager for setting runtime context variables."""
    ctx = _runtime_context.get() or RuntimeContext()
    token = _runtime_context.set(ctx)
    try:
        yield ctx
    finally:
        _runtime_context.reset(token)