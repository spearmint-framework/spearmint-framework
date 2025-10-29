"""Multi-branch concurrent execution strategy.

Executes all configurations concurrently and returns a `BranchContainer` with
all collected branch results.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from ..branch import BranchContainer
from .base import Strategy


class SingleConfigStrategy(Strategy):
    """Strategy that executes the same single config."""

    async def run(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> BranchContainer:
        """Execute function concurrently with all configs.

        Args:
            func: Async function to execute
            *args: Positional arguments to pass to func
            **kwargs: Keyword arguments to pass to func

        Returns:
            BranchContainer with all execution results

        Raises:
            ValueError: If configs is empty
        """
        if not self.configs:
            raise ValueError("SingleConfigStrategy requires one config")

        config = self.configs[0]
        config_id = self._generate_config_id(config)
        bound_configs = self._bind_config(config)
        branch = await self._execute_branch(func, bound_configs, config_id, *args, **kwargs)

        if branch.status == "failed" and branch.exception_info is not None:
            exc_type = branch.exception_info["type"]
            exc_message = branch.exception_info["message"]
            raise RuntimeError(f"{exc_type}: {exc_message}")

        return branch.output


__all__ = ["SingleConfigStrategy"]
