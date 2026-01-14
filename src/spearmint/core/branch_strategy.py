import asyncio
import inspect
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .branch import Branch, BranchExecType
from .config import Config
from .plan_executor import current_path_config
from .run_wrapper import RunWrapper


class BranchStrategy(RunWrapper):
    def __init__(
        self, func: Callable[..., Any], configs: list[Config], bindings: dict[type[BaseModel], str]
    ) -> None:
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
    def sequential_branches(self) -> list[Branch]:
        return [branch for branch in self.branches if branch.exec_type == BranchExecType.SEQUENTIAL]

    @property
    def parallel_branches(self) -> list[Branch]:
        return [branch for branch in self.branches if branch.exec_type == BranchExecType.PARALLEL]

    @property
    def background_branches(self) -> list[Branch]:
        return [branch for branch in self.branches if branch.exec_type == BranchExecType.BACKGROUND]

    @property
    def noop_branches(self) -> list[Branch]:
        return [branch for branch in self.branches if branch.exec_type == BranchExecType.NOOP]

    @property
    def output(self) -> Any:
        return self.default_branch.output

    async def run(
        self,
        *args: Any,
        wait_for_background: bool = False,
        return_all: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Run all branches according to their execution types.

        Args:
            *args: Positional arguments to pass to branch functions.
            wait_for_background: If True, wait for background branches to complete.
            return_all: If True, return list of all branches instead of default output.
            **kwargs: Keyword arguments to pass to branch functions.

        Returns:
            If return_all is True, returns list of Branch objects.
            Otherwise, returns the default branch output.
        """
        background_tasks: list[asyncio.Task[Any]] = []

        async with self.wrapped():
            for branch in self.sequential_branches:
                await branch.run(*args, **kwargs)

            tasks = []
            for branch in self.parallel_branches:
                # Create task with context inheritance via direct awaitable
                task = asyncio.create_task(branch.run(*args, **kwargs))
                tasks.append(task)
            await asyncio.gather(*tasks, return_exceptions=False)

            for branch in self.background_branches:
                task = asyncio.create_task(branch.run(*args, **kwargs))
                background_tasks.append(task)

        if wait_for_background and background_tasks:
            await asyncio.gather(*background_tasks, return_exceptions=True)

        if return_all:
            return self.branches

        return self.output

    def _create_branches(
        self,
        func: Callable[..., Any],
        configs: list[Config],
        bindings: dict[type[BaseModel], str],
        *args: Any,
        **kwargs: Any,
    ) -> list[Branch]:
        assignments = current_path_config.get()
        func_key = self._function_key(func)
        target_config_id = assignments.get(func_key)

        branches = []
        for config in configs:
            # If a plan has pre-assigned a config_id for this function, only
            # instantiate the matching branch. Otherwise, keep all configs.
            if target_config_id and str(config["config_id"]) != str(target_config_id):
                continue

            bound_configs = self._bind_config(config, bindings)
            branch = Branch(func=func, configs=bound_configs, config_id=config["config_id"])
            branches.append(branch)

        # Fallback: if filtering removed everything, revert to original configs
        if not branches:
            for config in configs:
                bound_configs = self._bind_config(config, bindings)
                branch = Branch(func=func, configs=bound_configs, config_id=config["config_id"])
                branches.append(branch)

        return branches

    def _function_key(self, func: Callable[..., Any]) -> str:
        """Best-effort key that matches introspector output.

        The introspector uses "relative_path:func_name" with paths relative
        to the repository root. Here we approximate using cwd as the root.
        """
        try:
            path = Path(inspect.getsourcefile(func) or "").resolve()
            rel = path.relative_to(Path.cwd())
            return f"{rel.as_posix()}:{func.__name__}"
        except Exception:
            return func.__name__

    def _bind_config(self, config: Config, bindings: dict[type[BaseModel], str]) -> list[BaseModel]:
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
