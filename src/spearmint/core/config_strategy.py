import random
from collections.abc import Generator
from contextlib import AsyncExitStack
from typing import Any

from .run_wrapper import RunWrapper, on_run


class ConfigStrategy(RunWrapper):
    def __init__(self, context: Any) -> None:
        self.context = context
        self.branches: list[Any] = []

    @property
    def default_branch(self) -> Any:
        for branch in self.branches:
            if branch.default:
                return branch
        return None

    def set_default_branch(self, branch: Any) -> None:
        for b in self.branches:
            b.default = False
        branch.default = True

    @property
    def output(self) -> Any:
        return self.default_branch.output

    async def run(self, *args: Any, **kwargs: Any) -> Any:
        async with AsyncExitStack() as stack:
            # Enter all wrappers in order
            for wrapper in self.run_wrappers:
                await stack.enter_async_context(wrapper(self))

            # Execute the actual function once, after all wrappers are active
            for branch in self.branches:
                await branch.run(*args, **kwargs)

        return self.output


# TODO: move out to its own file in strategies/
class RandomConfigStrategy(ConfigStrategy):
    @on_run
    def select_random_branch(self) -> Generator[Any, None, None]:
        selected_branch = random.choice(self.branches)
        self.set_default_branch(selected_branch)
        for branch in self.branches:
            if branch != selected_branch:
                branch.run_strategy = "noop"

        yield
