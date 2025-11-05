"""Round-robin strategy implementation.

Executes one configuration per invocation, cycling sequentially through the
provided list of configs.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from spearmint.branch import BranchContainer

from .base import Strategy


class RoundRobinStrategy(Strategy):
    """Strategy that cycles through configs sequentially on each execution.

    Maintains an internal index that rotates through the config list,
    executing one config per call and returning its output directly.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the RoundRobinStrategy instance."""
        super().__init__(*args, **kwargs)
        self._index = 0

    async def run(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> tuple[Any, BranchContainer]:
        """Execute function with the next config in rotation.

        Args:
            func: Async function to execute
            configs: Sequence of configuration dictionaries
            *args: Positional arguments to pass to func
            **kwargs: Keyword arguments to pass to func

        Returns:
            Direct output from the executed function

        Raises:
            ValueError: If configs is empty
        """
        if not self.configs:
            raise ValueError("RoundRobinStrategy requires at least one config")

        config = self.configs[self._index]
        config_id = config["config_id"]
        bound_configs = self._bind_config(config)
        branch = await self._execute_branch(func, bound_configs, config_id, *args, **kwargs)

        self._index = (self._index + 1) % len(self.configs)

        if branch.status == "failed" and branch.exception_info is not None:
            exc_type = branch.exception_info["type"]
            exc_message = branch.exception_info["message"]
            raise RuntimeError(f"{exc_type}: {exc_message}")

        return branch.output, BranchContainer([branch])


__all__ = ["RoundRobinStrategy"]
