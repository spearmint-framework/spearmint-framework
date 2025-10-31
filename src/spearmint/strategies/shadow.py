"""Shadow execution strategy.

Runs a designated primary configuration in the foreground while executing all
other configurations in the background ("shadow" runs). Useful for comparing
results or validating that alternative configurations behave similarly without
impacting the primary flow.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from .base import Strategy


class ShadowStrategy(Strategy):
    """Execute primary config foreground, others as shadows.

    Returns the primary config result immediately while scheduling shadow
    executions in the background for comparison/testing purposes.
    """

    def __init__(self, *args: Any, primary_index: int = 0, **kwargs: Any) -> None:
        """Initialize the ShadowStrategy instance."""
        super().__init__(*args, **kwargs)
        self.primary_index = primary_index

        # Shadow tasks created after primary run; store Task objects (branches as results)
        self._shadow_tasks: list[Any] = []

    async def run(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute primary config foreground, schedule shadows in background.

        Args:
            func: Async function to execute
            *args: Positional arguments to pass to func
            **kwargs: Keyword arguments to pass to func

        Returns:
            Direct output from the primary config execution

        Raises:
            ValueError: If configs is empty or primary_index out of range
        """
        if not self.configs:
            raise ValueError("ShadowStrategy requires at least one config")
        if self.primary_index >= len(self.configs):
            raise ValueError(
                f"Primary index {self.primary_index} out of range for {len(self.configs)} configs"
            )

        primary_config = self.configs[self.primary_index]
        primary_config_id = primary_config["config_id"]
        bound_primary_config = self._bind_config(primary_config)
        primary_branch = await self._execute_branch(
            func, bound_primary_config, primary_config_id, *args, **kwargs
        )

        self._shadow_tasks = []
        for i, config in enumerate(self.configs):
            if i != self.primary_index:
                config_id = config["config_id"]
                bound_config = self._bind_config(config)
                task = asyncio.create_task(
                    self._execute_branch(func, bound_config, config_id, *args, **kwargs)
                )
                self._shadow_tasks.append(task)

        if primary_branch.status == "failed" and primary_branch.exception_info is not None:
            exc_type = primary_branch.exception_info["type"]
            exc_message = primary_branch.exception_info["message"]
            raise RuntimeError(f"{exc_type}: {exc_message}")

        return primary_branch.output

    async def gather_shadows(self) -> list[Any]:
        """Await all shadow task completions and return their branches.

        Returns:
            List of Branch instances from shadow executions
        """
        if not self._shadow_tasks:
            return []
        return await asyncio.gather(*self._shadow_tasks, return_exceptions=False)


__all__ = ["ShadowStrategy"]
