"""Spearmint Framework.

A framework for experimentation with LLMs and document processing.
"""

import asyncio
import inspect
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from spearmint.core.branch_strategy import BranchStrategy
from spearmint.core.config import Config, parse_configs
from spearmint.core.introspection import ExperimentIntrospector, ExperimentPlan
from spearmint.core.plan_executor import PlanExecutor, get_assigned_config_id
from spearmint.core.run_session import RunSession
from spearmint.core.utils.handlers import jsonl_handler, yaml_handler
from spearmint.strategies import DefaultBranchStrategy


class Spearmint:
    """Main Spearmint class for managing experiments and strategies."""

    def __init__(
        self,
        branch_strategy: type[BranchStrategy] | None = None,
        configs: list[dict[str, Any] | Config | str | Path] | None = None,
        bindings: dict[type[BaseModel], str] | None = None,
        evaluators: list[Callable[..., Any]] | None = None,
    ) -> None:
        self._config_handler: Callable[[str | Path], list[dict[str, Any]]] = yaml_handler
        self._dataset_handler: Callable[[str | Path], list[dict[str, Any]]] = jsonl_handler
        self.branch_strategy: type[BranchStrategy] = branch_strategy or DefaultBranchStrategy
        self.configs: list[Config] = parse_configs(configs or [], self._config_handler)
        self.bindings: dict[type[BaseModel], str] = {Config: ""} if bindings is None else bindings
        self.evaluators: list[Callable[..., Any]] = evaluators or []

    def run(
        self,
        func: Callable[..., Any],
        *,
        return_all: bool = True,
        wait_for_background: bool = True,
    ) -> RunSession:
        """Create a RunSession context manager for executing an experiment.

        This provides an ergonomic API for running experiments and collecting
        results from all branches in a structured format.

        Args:
            func: The main function to execute within the experiment context.
            return_all: If True, return results from all branches formatted
                       as a list of records with config_chain and outputs.
                       If False, return only the default branch output.
            wait_for_background: If True, wait for background branches to
                                complete before returning results.

        Returns:
            A RunSession async context manager.

        Example:
            >>> async with mint.run(main) as runner:
            ...     results = await runner(
            ...         step1_input="example",
            ...         step2_input="data",
            ...     )
            ...     # results is a list of branch records
        """
        return RunSession(
            func=func,
            return_all=return_all,
            wait_for_background=wait_for_background,
        )

    def plan(
        self,
        entry_file: Path | str,
        entry_func: str | None = None,
        *,
        follow_imports: bool = True,
        repo_root: Path | str | None = None,
    ) -> ExperimentPlan:
        """Analyze source code to build a precomputed experiment plan.

        This performs static analysis to discover all experiment-decorated
        functions, their configurations, and call relationships. The resulting
        plan enumerates all execution paths with pre-assigned config IDs.

        Args:
            entry_file: Path to the Python file containing the entry point.
            entry_func: Name of the entry function (uses first found if None).
            follow_imports: If True, follow imports to discover more experiments.
            repo_root: Repository root for resolving imports. Defaults to cwd.

        Returns:
            ExperimentPlan with enumerated paths and config assignments.

        Example:
            >>> plan = mint.plan("main.py", "run_experiment")
            >>> print(f"Found {len(plan.paths)} execution paths")
            >>> for path in plan.paths:
            ...     print(f"  {path.path_id}: {path.config_assignments}")
        """
        entry_path = Path(entry_file)
        root = Path(repo_root) if repo_root else None

        introspector = ExperimentIntrospector(repo_root=root)
        return introspector.build_plan(
            entry_file=entry_path,
            entry_func=entry_func,
            follow_imports=follow_imports,
        )

    def run_plan(
        self,
        plan: ExperimentPlan,
        entry_func: Callable[..., Any],
        *,
        max_workers: int | None = None,
    ) -> "PlanRunner":
        """Create a PlanRunner for executing a precomputed plan.

        This executes all paths in the plan in parallel, with each path
        using its pre-assigned config IDs. This ensures nested experiments
        follow all paths instead of just returning the foreground response.

        Args:
            plan: The precomputed experiment plan from mint.plan().
            entry_func: The entry point function to execute.
            max_workers: Maximum parallel workers (default: number of paths).

        Returns:
            A PlanRunner async context manager.

        Example:
            >>> plan = mint.plan("main.py", "run_experiment")
            >>> async with mint.run_plan(plan, run_experiment) as runner:
            ...     results = await runner(input_data="test")
            ...     for r in results.path_results:
            ...         print(f"{r.path_id}: {r.output}")
        """
        return PlanRunner(
            plan=plan,
            entry_func=entry_func,
            max_workers=max_workers,
        )

    def experiment(
        self,
        branch_strategy: type[BranchStrategy] | None = None,
        configs: list[dict[str, Any] | Config | str | Path] | None = None,
        bindings: dict[type[BaseModel], str] | None = None,
        evaluators: list[Callable[..., Any]] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for wrapping functions with experiment execution strategy."""
        evaluators = evaluators or self.evaluators

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return self.configure(
                branch_strategy=branch_strategy,
                configs=configs,
                bindings=bindings,
            )(func)

        return decorator

    def configure(
        self,
        branch_strategy: type[BranchStrategy] | None = None,
        configs: list[dict[str, Any] | Config | str | Path] | None = None,
        bindings: dict[type[BaseModel], str] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for wrapping functions with experiment execution strategy."""
        branch_strategy = branch_strategy or self.branch_strategy
        bindings = bindings or self.bindings
        parsed_configs = parse_configs(configs or self.configs or [], yaml_handler)
        bindings = {Config: ""} if bindings is None else bindings

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def awrapper(*args: Any, **kwargs: Any) -> Any:
                branch_strategy_instance = branch_strategy(
                    func=func, configs=parsed_configs, bindings=bindings
                )
                return await branch_strategy_instance.run(*args, **kwargs)

            @wraps(func)
            def swrapper(*args: Any, **kwargs: Any) -> Any:
                import contextvars
                
                # Capture the current context to propagate to the async execution
                ctx = contextvars.copy_context()
                
                async def run_with_context() -> Any:
                    return await awrapper(*args, **kwargs)
                
                try:
                    loop = asyncio.get_running_loop()
                    # Already in an event loop - we need to run in the same loop
                    # Use asyncio.ensure_future and run until complete won't work
                    # Instead, we need to schedule and wait
                    import concurrent.futures
                    
                    def run_in_new_loop() -> Any:
                        # Run with copied context
                        return ctx.run(asyncio.run, run_with_context())
                    
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_new_loop)
                        return future.result()
                except RuntimeError:
                    # No running loop - run with context preserved
                    return ctx.run(asyncio.run, run_with_context())

            return awrapper if inspect.iscoroutinefunction(func) else swrapper

        return decorator


def experiment(
    branch_strategy: type[BranchStrategy],
    configs: list[dict[str, Any] | Config | str | Path],
    bindings: dict[type[BaseModel], str] | None = None,
    evaluators: list[Callable[..., Any]] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for wrapping functions with experiment execution strategy.

    This decorator wraps an async function and orchestrates its execution
    through the provided strategy, handling config injection and logging.

    Args:
        strategy: Strategy instance to use for execution

    Returns:
        Decorator function

    Example:
        >>> @experiment()
        >>> async def my_func(x: int, config: dict) -> int:
        ...     return x + config['delta']
        >>>
        >>> result = await my_func(10)
    """
    spearmint_instance = Spearmint(
        branch_strategy=branch_strategy,
        configs=configs,
        bindings=bindings,
        evaluators=evaluators,
    )
    return spearmint_instance.experiment()


def configure(
    branch_strategy: type[BranchStrategy],
    configs: list[dict[str, Any] | Config | str | Path],
    bindings: dict[type[BaseModel], str] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for wrapping functions with experiment execution strategy.

    This decorator wraps an async function and orchestrates its execution
    through the provided strategy, handling config injection and logging.

    Args:
        strategy: Strategy instance to use for execution

    Returns:
        Decorator function

    Example:
        >>> @configure()
        >>> async def my_func(x: int, config: dict) -> int:
        ...     return x + config['delta']
        >>>
        >>> result = await my_func(10)
    """
    spearmint_instance = Spearmint()
    return spearmint_instance.configure(
        branch_strategy=branch_strategy,
        configs=configs,
        bindings=bindings,
    )


class PlanRunner:
    """Async context manager for executing a precomputed experiment plan.

    Executes all paths in the plan in parallel, ensuring nested experiments
    follow all paths by using pre-assigned config IDs.

    Example:
        >>> plan = mint.plan("main.py", "run_experiment")
        >>> async with mint.run_plan(plan, run_experiment) as runner:
        ...     results = await runner(input_data="test")
    """

    def __init__(
        self,
        plan: ExperimentPlan,
        entry_func: Callable[..., Any],
        max_workers: int | None = None,
    ) -> None:
        """Initialize the PlanRunner.

        Args:
            plan: The precomputed experiment plan.
            entry_func: The entry point function to execute.
            max_workers: Maximum parallel workers.
        """
        self.plan = plan
        self.entry_func = entry_func
        self.max_workers = max_workers
        self._executor: PlanExecutor | None = None

    async def __aenter__(self) -> "PlanRunner":
        """Enter the async context."""
        self._executor = PlanExecutor(
            plan=self.plan,
            max_workers=self.max_workers,
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the async context."""
        self._executor = None

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute all paths in the plan.

        Args:
            *args: Positional arguments to pass to the entry function.
            **kwargs: Keyword arguments to pass to the entry function.

        Returns:
            PlanExecutionResult with results from all paths.
        """
        if self._executor is None:
            raise RuntimeError("PlanRunner must be used as async context manager")

        return await self._executor.execute(self.entry_func, *args, **kwargs)
