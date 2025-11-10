import random
from collections.abc import Generator
from typing import Any

from spearmint.core.branch_strategy import BranchStrategy
from spearmint.core.branch import BranchExecType
from spearmint.core.run_wrapper import on_run

class MultiBranchStrategy(BranchStrategy):
    @on_run
    def parallelize_branches(self) -> Generator[Any, None, None]:
        for branch in self.branches:
            branch.exec_type = BranchExecType.PARALLEL

        yield