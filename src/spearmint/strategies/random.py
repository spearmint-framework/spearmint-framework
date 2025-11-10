import random
from collections.abc import Generator
from typing import Any

from spearmint.core.branch_strategy import BranchStrategy
from spearmint.core.branch import BranchExecType
from spearmint.core.run_wrapper import on_run

class RandomBranchStrategy(BranchStrategy):
    @on_run
    def select_random_branch(self) -> Generator[Any, None, None]:
        # Randomly select one branch to execute
        selected_branch = random.choice(self.branches)
        self.default_branch = selected_branch

        # Set all other branches to NOOP
        for branch in self.branches:
            if branch != selected_branch:
                branch.exec_type = BranchExecType.NOOP

        yield