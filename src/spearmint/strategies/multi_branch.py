import random
from collections.abc import AsyncGenerator, Generator
from typing import Any

from spearmint.core.branch_strategy import BranchStrategy
from spearmint.core.branch import BranchExecType, Branch
from spearmint.core.run_wrapper import on_run

class MultiBranchStrategy(BranchStrategy):

    @property
    def output(self) -> list[Branch]:
        return self.branches

    @on_run
    async def parallelize_branches(self) -> AsyncGenerator[Any, None, None]:
        for branch in self.branches:
            branch.exec_type = BranchExecType.PARALLEL

        yield