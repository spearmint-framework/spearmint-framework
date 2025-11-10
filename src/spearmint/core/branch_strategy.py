import asyncio
from copy import deepcopy
import random
from collections.abc import Generator
from contextlib import AsyncExitStack
from typing import Any, Callable

from pydantic import BaseModel

from .branch import Branch, BranchExecType
from .run_wrapper import RunWrapper, on_run
from .config import Config


class BranchStrategy(RunWrapper):
    def __init__(self, func: Callable[..., Any], configs: list[Config], bindings: dict[str, Any]) -> None:
        self.branches: list[Branch] = self._create_branches(func, configs, bindings)

    @property
    def default_branch(self) -> Branch:
        for branch in self.branches:
            if branch.default:
                return branch
        return self.branches[0]

    @default_branch.setter
    def default_branch(self, branch: Branch) -> None:
        for b in self.branches:
            b.default = False
        branch.default = True

    @property
    def sequential_branches(self) -> bool:
        return all(branch.exec_type == BranchExecType.SEQUENTIAL for branch in self.branches)

    @property
    def parallel_branches(self) -> bool:
        return all(branch.exec_type == BranchExecType.PARALLEL for branch in self.branches)
    
    @property
    def background_branches(self) -> bool:
        return all(branch.exec_type == BranchExecType.BACKGROUND for branch in self.branches)

    @property
    def noop_branches(self) -> bool:
        return all(branch.exec_type == BranchExecType.NOOP for branch in self.branches)

    @property
    def output(self) -> Any:
        return self.default_branch.output

    async def run(self, *args: Any, **kwargs: Any) -> Any:
        async with self.wrapped():
            for branch in self.sequential_branches:
                await branch.run(*args, **kwargs)

            tasks = []
            for branch in self.parallel_branches:
                task = asyncio.create_task(branch.run(*args, **kwargs))
                tasks.append(task)
            await asyncio.gather(*tasks, return_exceptions=False)

            for branch in self.background_branches:
                asyncio.create_task(branch.run(*args, **kwargs))

        return self.output
    
    def _create_branches(
        self,
        func: Callable[..., Any],
        configs: list[Config],
        bindings: dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> list[Branch]:
        branches = []
        for config in configs:
            bound_configs = self._bind_config(config, bindings)
            branch = Branch(func=func, configs=bound_configs)
            branches.append(branch)
        return branches

    def _bind_config(self, config: Config, bindings: dict[str, Any]) -> list[BaseModel]:
        """Bind configs to model classes based on provided bindings.

        This method can be used to map configuration model instances
        to function parameters based on type annotations or explicit
        bindings.
        """
        bound_configs = []

        for model_cls, bind_path in bindings.items():
            # For RootModel, model_dump() returns the root dict
            config_dict = config.model_dump() if hasattr(config, "model_dump") else config.root
            config_data = deepcopy(config_dict)
            parts = bind_path.split(".")
            for part in parts:
                if not part:
                    continue
                if part in config_data:
                    config_data = config_data[part]
                else:
                    raise ValueError(f"Key '{part}' not found in bind path '{bind_path}'")

            bound_configs.append(model_cls.model_validate(config_data))

        return bound_configs
