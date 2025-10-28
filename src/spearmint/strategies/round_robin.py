"""Round-robin strategy implementation.

Executes one configuration per invocation, cycling sequentially through the
provided list of configs.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from ..logging import LoggerBackend
from .base import _execute_branch


class RoundRobinStrategy:
    """Strategy that cycles through configs sequentially on each execution.

    Maintains an internal index that rotates through the config list,
    executing one config per call and returning its output directly.
    """

    def __init__(self) -> None:  # noqa: D401
        self._index = 0

    async def run(
        self,
        func: Callable[..., Awaitable[Any]],
        configs: Sequence[dict[str, Any]],
        *args: Any,
        logger: LoggerBackend | None = None,
        **kwargs: Any,
    ) -> Any:
        """Execute function with the next config in rotation.

        Args:
            func: Async function to execute
            configs: Sequence of configuration dictionaries
            *args: Positional arguments to pass to func
            logger: Optional logger backend
            **kwargs: Keyword arguments to pass to func

        Returns:
            Direct output from the executed function

        Raises:
            ValueError: If configs is empty
        """
        if not configs:
            raise ValueError("RoundRobinStrategy requires at least one config")

        config = configs[self._index]
        config_id = f"round_robin_{self._index}"
        branch = await _execute_branch(func, config, config_id, logger, *args, **kwargs)

        self._index = (self._index + 1) % len(configs)

        if branch.status == "failed" and branch.exception_info is not None:
            exc_type = branch.exception_info["type"]
            exc_message = branch.exception_info["message"]
            raise RuntimeError(f"{exc_type}: {exc_message}")

        return branch.output


__all__ = ["RoundRobinStrategy"]
