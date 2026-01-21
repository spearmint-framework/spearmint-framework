"""Context variables for Spearmint execution."""

from __future__ import annotations

from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, AsyncIterator

from .experiment_function import ExperimentCase

if TYPE_CHECKING:
    from .runner import ExperimentRunner


current_experiment_case: ContextVar[ExperimentCase | None] = ContextVar(
    "spearmint_experiment_case", default=None
)

experiment_runner: ContextVar["ExperimentRunner | None"] = ContextVar(
    "spearmint_experiment_runner", default=None
)


@asynccontextmanager
async def set_experiment_case(experiment_case: ExperimentCase) -> AsyncIterator[None]:
    token = current_experiment_case.set(experiment_case)
    try:
        yield
    finally:
        current_experiment_case.reset(token)