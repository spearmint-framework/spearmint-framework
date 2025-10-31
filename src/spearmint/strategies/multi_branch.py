"""Multi-branch concurrent execution strategy.

Executes all configurations concurrently and returns a `BranchContainer` with
all collected branch results.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from ..branch import BranchContainer
from .base import Strategy


class MultiBranchStrategy(Strategy):
    """Strategy that executes all configs concurrently.

    Fans out execution across all configs in parallel and returns a
    BranchContainer with all results.
    """

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
            raise ValueError("MultiBranchStrategy requires at least one config")

        tasks = []
        for config in self.configs:
            config_id = config["config_id"]
            bound_config = self._bind_config(config)
            task = self._execute_branch(func, bound_config, config_id, *args, **kwargs)
            tasks.append(task)

        branches = await asyncio.gather(*tasks, return_exceptions=False)

        return BranchContainer(list(branches))


__all__ = ["MultiBranchStrategy"]
