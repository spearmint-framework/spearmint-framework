from collections.abc import Callable
from contextlib import AsyncExitStack
from typing import Any

from .run_wrapper import RunWrapper


class Experiment(RunWrapper):
    """Base class for all Experiments in Spearmint.

    Experiments define the core logic for running a set of configurations
    and collecting results. They can be extended to implement custom
    behavior for specific types of experiments.
    """

    def __init__(self, func: Callable[..., Any]) -> None:
        self.func: Callable[..., Any] = func
        self.results: list[Any] = []

    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the experiment with the given arguments.

        This method should be overridden by subclasses to implement
        specific experiment logic.

        Args:
            *args: Positional arguments for the experiment.
            **kwargs: Keyword arguments for the experiment.

        Returns:
            The result of the experiment run.
        """

        async with AsyncExitStack() as stack:
            # Enter all wrappers in order
            for wrapper in self.run_wrappers:
                await stack.enter_async_context(wrapper(self))

            result = await self.func(*args, **kwargs)
            self.evaluate()
            return result

    def evaluate(self) -> None:
        e = Evaluator()
        for branch in self.results:
            e.run(branch)
