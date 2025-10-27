"""Multi-branch concurrent execution strategy.

Executes all configurations concurrently and returns a `BranchContainer` with
all collected branch results.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from ..branch import BranchContainer
from ..logging import LoggerBackend
from .base import _execute_branch


class MultiBranchStrategy:
    """Strategy that executes all configs concurrently.

    Fans out execution across all configs in parallel and returns a
    BranchContainer with all results.
    """

    async def run(
        self,
        func: Callable[..., Awaitable[Any]],
        configs: Sequence[dict[str, Any]],
        *args: Any,
        logger: LoggerBackend | None = None,
        **kwargs: Any,
    ) -> BranchContainer:
        """Execute function concurrently with all configs.

        Args:
            func: Async function to execute
            configs: Sequence of configuration dictionaries
            *args: Positional arguments to pass to func
            logger: Optional logger backend
            **kwargs: Keyword arguments to pass to func

        Returns:
            BranchContainer with all execution results

        Raises:
            ValueError: If configs is empty
        """
        if not configs:
            raise ValueError("MultiBranchStrategy requires at least one config")

        tasks = []
        for i, config in enumerate(configs):
            config_id = f"multi_branch_{i}"
            task = _execute_branch(func, config, config_id, logger, *args, **kwargs)
            tasks.append(task)

        branches = await asyncio.gather(*tasks, return_exceptions=False)

        return BranchContainer(list(branches))


__all__ = ["MultiBranchStrategy"]
