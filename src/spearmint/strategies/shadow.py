"""Shadow execution strategy.

Runs a designated primary configuration in the foreground while executing all
other configurations in the background ("shadow" runs). Useful for comparing
results or validating that alternative configurations behave similarly without
impacting the primary flow.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from typing import Any, Generic

from .base import TModel, _execute_branch


class ShadowStrategy(Generic[TModel]):
    """Execute primary config foreground, others as shadows.

    Returns the primary config result immediately while scheduling shadow
    executions in the background for comparison/testing purposes.
    """

    def __init__(self, primary_index: int = 0) -> None:  # noqa: D401
        self.primary_index = primary_index

        # Shadow tasks created after primary run; store Task objects (branches as results)
        self._shadow_tasks = []  # type: list[asyncio.Task]

    async def run(
        self,
        func: Callable[..., Awaitable[Any]],
        configs: Sequence[TModel],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute primary config foreground, schedule shadows in background.

        Args:
            func: Async function to execute
            configs: Sequence of configuration dictionaries
            *args: Positional arguments to pass to func
            **kwargs: Keyword arguments to pass to func

        Returns:
            Direct output from the primary config execution

        Raises:
            ValueError: If configs is empty or primary_index out of range
        """
        if not configs:
            raise ValueError("ShadowStrategy requires at least one config")
        if self.primary_index >= len(configs):
            raise ValueError(
                f"Primary index {self.primary_index} out of range for {len(configs)} configs"
            )

        primary_config = configs[self.primary_index]
        primary_config_id = f"shadow_primary_{self.primary_index}"
        primary_branch = await _execute_branch(
            func, primary_config, primary_config_id, *args, **kwargs
        )

        self._shadow_tasks = []
        for i, config in enumerate(configs):
            if i != self.primary_index:
                config_id = f"shadow_{i}"
                task = asyncio.create_task(
                    _execute_branch(func, config, config_id, *args, **kwargs)
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
