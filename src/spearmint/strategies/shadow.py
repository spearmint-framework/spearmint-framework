import random
from collections.abc import AsyncGenerator
from typing import Any

from spearmint.core.branch_strategy import BranchStrategy
from spearmint.core.branch import BranchExecType
from spearmint.core.run_wrapper import on_run

class ShadowBranchStrategy(BranchStrategy):
    @on_run
    async def set_background_branches(self) -> AsyncGenerator[Any, None, None]:
        # get the default branch
        default_branch = self.default_branch

        # Set all other branches to run in background
        for branch in self.branches:
            if branch != default_branch:
                branch.exec_type = BranchExecType.BACKGROUND

        yield