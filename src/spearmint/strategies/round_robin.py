from typing import Any
from collections.abc import AsyncGenerator

from spearmint.core.branch_strategy import BranchStrategy
from spearmint.core.branch import BranchExecType
from spearmint.core.run_wrapper import on_run

INDEX = 0

class RoundRobinBranchStrategy(BranchStrategy):
    @on_run
    async def select_next_branch(self) -> AsyncGenerator[Any, None, None]:
        global INDEX
        # Select next branch as default
        default_branch = self.branches[INDEX]
        self.default_branch(default_branch)

        # Update INDEX for next run
        INDEX = (INDEX + 1) % len(self.branches)

        # Set all other branches to NOOP
        for branch in self.branches:
            if branch != default_branch:
                branch.exec_type = BranchExecType.NOOP

        yield
