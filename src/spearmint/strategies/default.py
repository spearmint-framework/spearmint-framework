from collections.abc import Generator
from typing import Any

from spearmint.core.branch_strategy import BranchStrategy
from spearmint.core.branch import BranchExecType
from spearmint.core.run_wrapper import on_run

class DefaultBranchStrategy(BranchStrategy):
    @on_run
    def default_branch(self) -> Generator[Any, None, None]:
        # Randomly select one branch to execute
        default_branch = self.default_branch
        default_branch.exec_type = BranchExecType.SEQUENTIAL

        # Set all other branches to NOOP
        for branch in self.branches:
            if branch != default_branch:
                branch.exec_type = BranchExecType.NOOP

        yield