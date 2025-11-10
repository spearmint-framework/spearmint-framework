from collections.abc import Callable
from contextlib import AsyncExitStack
from typing import Any


from .dependency_injector import inject_config
from .branch import Branch
from .run_wrapper import RunWrapper


class Experiment(RunWrapper):
    """Base class for all Experiments in Spearmint.

    Experiments define the core logic for running a set of configurations
    and collecting results. They can be extended to implement custom
    behavior for specific types of experiments.
    """

    def __init__(self, func: Callable[..., Any]) -> None:
        self.func: Callable[..., Any] = func
        self.branches: list[Branch] = []
        self.branch_evals: list[Any] = []
        self.evaluators: list[Callable[..., Any]] = []
        self.dependency_injector: Callable[..., Any] = inject_config
        self.output: Any = None

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
        async with self.wrapped():
            injected_args, injected_kwargs = self.dependency_injector(*args, **kwargs)

            self.output = await self.func(*injected_args, **injected_kwargs)
            self.evaluate()

        return self.output

    def evaluate(self) -> None:
        for evaluate in self.evaluators:
            for branch in self.branches:
                eval_result = evaluate(branch)
                self.branch_evals.append({
                    "branch": branch,
                    "result": eval_result
                })
