"""Integration tests for plan-based nested experiment execution.

This module tests the precomputed execution plan functionality,
verifying that nested experiments follow all paths correctly.
"""

import asyncio
import random
import tempfile
from pathlib import Path

import pytest

from spearmint import (
    Config,
    ExperimentIntrospector,
    PlanExecutor,
    Spearmint,
    configure,
)
from spearmint.strategies import DefaultBranchStrategy, MultiBranchStrategy


class TestExperimentIntrospector:
    """Test the static analysis introspection functionality."""

    def test_discover_experiments_from_file(self, tmp_path: Path):
        """Discover experiment-decorated functions from source file."""
        source = '''
from spearmint import configure, Config
from spearmint.strategies import MultiBranchStrategy

@configure(
    branch_strategy=MultiBranchStrategy,
    configs=[{"config_id": "cfg_a", "val": 1}, {"config_id": "cfg_b", "val": 2}],
)
def my_experiment(config: Config):
    return config["val"]
'''
        test_file = tmp_path / "test_exp.py"
        test_file.write_text(source)

        introspector = ExperimentIntrospector(repo_root=tmp_path)
        functions, call_graph = introspector.discover_experiments(
            test_file, follow_imports=False
        )

        assert len(functions) == 1
        func = list(functions.values())[0]
        assert func.name == "my_experiment"
        assert func.branch_strategy == "MultiBranchStrategy"
        assert func.config_count == 2
        assert set(func.config_ids) == {"cfg_a", "cfg_b"}

    def test_discover_nested_experiments(self, tmp_path: Path):
        """Discover nested experiment function calls."""
        source = '''
from spearmint import configure, Config
from spearmint.strategies import MultiBranchStrategy

@configure(
    branch_strategy=MultiBranchStrategy,
    configs=[{"config_id": "inner_a"}, {"config_id": "inner_b"}],
)
def inner_func(config: Config):
    return config["config_id"]

@configure(
    branch_strategy=MultiBranchStrategy,
    configs=[{"config_id": "outer_x"}, {"config_id": "outer_y"}],
)
def outer_func(config: Config):
    result = inner_func()
    return f"{config['config_id']}:{result}"
'''
        test_file = tmp_path / "nested_exp.py"
        test_file.write_text(source)

        introspector = ExperimentIntrospector(repo_root=tmp_path)
        functions, call_graph = introspector.discover_experiments(
            test_file, follow_imports=False
        )

        assert len(functions) == 2
        assert "nested_exp.py:inner_func" in functions
        assert "nested_exp.py:outer_func" in functions

        # outer_func should call inner_func
        outer_key = "nested_exp.py:outer_func"
        inner_key = "nested_exp.py:inner_func"
        assert inner_key in call_graph.get(outer_key, set())

    def test_build_plan_enumerates_paths(self, tmp_path: Path):
        """Build plan should enumerate all config combinations."""
        source = '''
from spearmint import configure, Config
from spearmint.strategies import MultiBranchStrategy

@configure(
    branch_strategy=MultiBranchStrategy,
    configs=[{"config_id": "inner_1"}, {"config_id": "inner_2"}],
)
def inner(config: Config):
    return config["config_id"]

@configure(
    branch_strategy=MultiBranchStrategy,
    configs=[{"config_id": "outer_A"}, {"config_id": "outer_B"}],
)
def outer(config: Config):
    return inner()
'''
        test_file = tmp_path / "plan_test.py"
        test_file.write_text(source)

        introspector = ExperimentIntrospector(repo_root=tmp_path)
        plan = introspector.build_plan(
            entry_file=test_file,
            entry_func="outer",
            follow_imports=False,
        )

        # Should have 2 outer * 2 inner = 4 paths
        assert len(plan.paths) == 4

        # Verify all combinations exist
        combos = set()
        for path in plan.paths:
            outer_cfg = path.config_assignments.get("plan_test.py:outer")
            inner_cfg = path.config_assignments.get("plan_test.py:inner")
            combos.add((outer_cfg, inner_cfg))

        assert combos == {
            ("outer_A", "inner_1"),
            ("outer_A", "inner_2"),
            ("outer_B", "inner_1"),
            ("outer_B", "inner_2"),
        }


class TestPlanExecutor:
    """Test plan-based execution."""

    @pytest.mark.asyncio
    async def test_execute_simple_plan(self):
        """Execute a simple plan with single path."""
        from spearmint.core.introspection import ExperimentFunction, ExperimentPath, ExperimentPlan

        # Create a minimal plan
        func_key = "test:simple_func"
        plan = ExperimentPlan(
            functions={
                func_key: ExperimentFunction(
                    key=func_key,
                    name="simple_func",
                    file_path=Path("test.py"),
                    lineno=1,
                    is_async=True,
                    branch_strategy=None,
                    config_count=1,
                    config_ids=["cfg1"],
                )
            },
            call_graph={func_key: set()},
            paths=[
                ExperimentPath(
                    path_id="path1",
                    config_assignments={func_key: "cfg1"},
                    function_order=[func_key],
                )
            ],
            root_key=func_key,
        )

        async def entry_func(x: int) -> int:
            return x * 2

        executor = PlanExecutor(plan)
        result = await executor.execute(entry_func, 21)

        assert len(result.path_results) == 1
        assert result.path_results[0].output == 42
        assert result.path_results[0].success is True
        assert result.default_output == 42

    @pytest.mark.asyncio
    async def test_execute_multiple_paths(self):
        """Execute plan with multiple paths in parallel."""
        from spearmint.core.introspection import ExperimentFunction, ExperimentPath, ExperimentPlan

        func_key = "test:multi_func"
        plan = ExperimentPlan(
            functions={
                func_key: ExperimentFunction(
                    key=func_key,
                    name="multi_func",
                    file_path=Path("test.py"),
                    lineno=1,
                    is_async=True,
                    branch_strategy=None,
                    config_count=3,
                    config_ids=["cfg1", "cfg2", "cfg3"],
                )
            },
            call_graph={func_key: set()},
            paths=[
                ExperimentPath(
                    path_id=f"path{i}",
                    config_assignments={func_key: f"cfg{i}"},
                    function_order=[func_key],
                )
                for i in range(1, 4)
            ],
            root_key=func_key,
        )

        call_count = 0

        async def entry_func(multiplier: int) -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Simulate async work
            return multiplier * call_count

        executor = PlanExecutor(plan)
        result = await executor.execute(entry_func, 10)

        assert len(result.path_results) == 3
        assert all(r.success for r in result.path_results)
        # All three paths should have executed
        assert call_count == 3


class TestNestedExperimentExecution:
    """Test that nested experiments execute all paths correctly."""

    @pytest.mark.asyncio
    async def test_nested_experiment_all_paths_with_plan(self):
        """Verify nested experiments follow all paths when using plan execution."""
        # This test demonstrates the difference between traditional execution
        # (which only gets foreground results from nested experiments) vs
        # plan-based execution (which will run all path combinations).
        
        from spearmint.core.introspection import ExperimentFunction, ExperimentPath, ExperimentPlan
        
        # Create a manual plan that represents fn_main -> fn_nested
        # with 2 outer configs * 2 inner configs = 4 paths
        outer_key = "test:fn_main"
        inner_key = "test:fn_nested"
        
        plan = ExperimentPlan(
            functions={
                outer_key: ExperimentFunction(
                    key=outer_key,
                    name="fn_main",
                    file_path=Path("test.py"),
                    lineno=1,
                    is_async=False,
                    branch_strategy="MultiBranchStrategy",
                    config_count=2,
                    config_ids=["outer_1", "outer_2"],
                ),
                inner_key: ExperimentFunction(
                    key=inner_key,
                    name="fn_nested",
                    file_path=Path("test.py"),
                    lineno=10,
                    is_async=False,
                    branch_strategy="MultiBranchStrategy",
                    config_count=2,
                    config_ids=["inner_a", "inner_b"],
                ),
            },
            call_graph={outer_key: {inner_key}, inner_key: set()},
            paths=[
                ExperimentPath(
                    path_id="path_1",
                    config_assignments={outer_key: "outer_1", inner_key: "inner_a"},
                    function_order=[outer_key, inner_key],
                ),
                ExperimentPath(
                    path_id="path_2",
                    config_assignments={outer_key: "outer_1", inner_key: "inner_b"},
                    function_order=[outer_key, inner_key],
                ),
                ExperimentPath(
                    path_id="path_3",
                    config_assignments={outer_key: "outer_2", inner_key: "inner_a"},
                    function_order=[outer_key, inner_key],
                ),
                ExperimentPath(
                    path_id="path_4",
                    config_assignments={outer_key: "outer_2", inner_key: "inner_b"},
                    function_order=[outer_key, inner_key],
                ),
            ],
            root_key=outer_key,
        )
        
        results_collected: list[tuple[str, str]] = []
        
        def fn_main_impl(outer_cfg: str, inner_cfg: str) -> str:
            """Simulates the combined execution path."""
            # Inner function returns max // 2
            inner_values = {"inner_a": 50, "inner_b": 100}
            val = inner_values[inner_cfg]
            
            # Outer function compares to threshold
            thresholds = {"outer_1": 50, "outer_2": 150}
            threshold = thresholds[outer_cfg]
            
            results_collected.append((outer_cfg, inner_cfg))
            
            if val > threshold:
                return "BIG"
            else:
                return "not big"
        
        async def entry_func() -> list[str]:
            """Entry function that would be run for each path."""
            # In real plan execution, the current_path_config context var
            # would provide the config assignments
            from spearmint.core.plan_executor import current_path_config
            
            assignments = current_path_config.get()
            outer_cfg = assignments.get(outer_key, "outer_1")
            inner_cfg = assignments.get(inner_key, "inner_a")
            
            return fn_main_impl(outer_cfg, inner_cfg)
        
        executor = PlanExecutor(plan)
        result = await executor.execute(entry_func)
        
        # Should have executed all 4 paths
        assert len(result.path_results) == 4
        assert len(results_collected) == 4
        
        # Verify all combinations were executed
        assert set(results_collected) == {
            ("outer_1", "inner_a"),
            ("outer_1", "inner_b"),
            ("outer_2", "inner_a"),
            ("outer_2", "inner_b"),
        }
        
        # Verify expected outputs based on logic:
        # inner_a (50) vs outer_1 (50): not big (50 > 50 is false)
        # inner_b (100) vs outer_1 (50): BIG
        # inner_a (50) vs outer_2 (150): not big
        # inner_b (100) vs outer_2 (150): not big
        outputs = {r.path_id: r.output for r in result.path_results}
        expected = {
            "path_1": "not big",  # outer_1 + inner_a
            "path_2": "BIG",      # outer_1 + inner_b
            "path_3": "not big",  # outer_2 + inner_a
            "path_4": "not big",  # outer_2 + inner_b
        }
        assert outputs == expected

    @pytest.mark.asyncio
    async def test_spearmint_plan_api(self, tmp_path: Path):
        """Test the Spearmint.plan() API."""
        source = '''
from spearmint import configure, Config
from spearmint.strategies import MultiBranchStrategy

@configure(
    branch_strategy=MultiBranchStrategy,
    configs=[{"config_id": "a"}, {"config_id": "b"}],
)
def experiment_func(config: Config):
    return config["config_id"]
'''
        test_file = tmp_path / "exp.py"
        test_file.write_text(source)

        sp = Spearmint()
        plan = sp.plan(test_file, "experiment_func", follow_imports=False, repo_root=tmp_path)

        assert plan.root_key == "exp.py:experiment_func"
        assert len(plan.paths) == 2
        assert len(plan.functions) == 1

    @pytest.mark.asyncio
    async def test_plan_runner_context_manager(self):
        """Test PlanRunner as async context manager."""
        from spearmint.core.introspection import ExperimentFunction, ExperimentPath, ExperimentPlan

        func_key = "test:runner_func"
        plan = ExperimentPlan(
            functions={
                func_key: ExperimentFunction(
                    key=func_key,
                    name="runner_func",
                    file_path=Path("test.py"),
                    lineno=1,
                    is_async=True,
                    branch_strategy=None,
                    config_count=2,
                    config_ids=["c1", "c2"],
                )
            },
            call_graph={func_key: set()},
            paths=[
                ExperimentPath(
                    path_id="p1",
                    config_assignments={func_key: "c1"},
                    function_order=[func_key],
                ),
                ExperimentPath(
                    path_id="p2",
                    config_assignments={func_key: "c2"},
                    function_order=[func_key],
                ),
            ],
            root_key=func_key,
        )

        async def my_func(value: str) -> str:
            return f"result_{value}"

        sp = Spearmint()
        async with sp.run_plan(plan, my_func) as runner:
            result = await runner("test")

        assert len(result.path_results) == 2
        assert all(r.output == "result_test" for r in result.path_results)

    @pytest.mark.asyncio
    async def test_plan_execution_result_formatting(self):
        """Test PlanExecutionResult.as_records() formatting."""
        from spearmint.core.introspection import ExperimentFunction, ExperimentPath, ExperimentPlan

        func_key = "test:format_func"
        plan = ExperimentPlan(
            functions={
                func_key: ExperimentFunction(
                    key=func_key,
                    name="format_func",
                    file_path=Path("test.py"),
                    lineno=1,
                    is_async=True,
                    branch_strategy=None,
                    config_count=1,
                    config_ids=["cfg"],
                )
            },
            call_graph={func_key: set()},
            paths=[
                ExperimentPath(
                    path_id="path_x",
                    config_assignments={func_key: "cfg"},
                    function_order=[func_key],
                )
            ],
            root_key=func_key,
        )

        async def entry(x: int) -> int:
            return x + 1

        executor = PlanExecutor(plan)
        result = await executor.execute(entry, 5)

        records = result.as_records()
        assert len(records) == 1
        assert records[0]["path_id"] == "path_x"
        assert records[0]["output"] == 6
        assert records[0]["success"] is True
        assert "config_chain" in records[0]
        assert "config_assignments" in records[0]


class TestSyncFunctionPlanExecution:
    """Test plan execution with synchronous functions."""

    @pytest.mark.asyncio
    async def test_sync_function_in_plan(self):
        """Sync functions should work in plan execution."""
        from spearmint.core.introspection import ExperimentFunction, ExperimentPath, ExperimentPlan

        func_key = "test:sync_func"
        plan = ExperimentPlan(
            functions={
                func_key: ExperimentFunction(
                    key=func_key,
                    name="sync_func",
                    file_path=Path("test.py"),
                    lineno=1,
                    is_async=False,
                    branch_strategy=None,
                    config_count=1,
                    config_ids=["sync_cfg"],
                )
            },
            call_graph={func_key: set()},
            paths=[
                ExperimentPath(
                    path_id="sync_path",
                    config_assignments={func_key: "sync_cfg"},
                    function_order=[func_key],
                )
            ],
            root_key=func_key,
        )

        def sync_entry(a: int, b: int) -> int:
            return a * b

        executor = PlanExecutor(plan)
        result = await executor.execute(sync_entry, 6, 7)

        assert result.default_output == 42
        assert result.path_results[0].success is True


class TestErrorHandlingInPlan:
    """Test error handling during plan execution."""

    @pytest.mark.asyncio
    async def test_exception_captured_in_path_result(self):
        """Exceptions should be captured in PathResult."""
        from spearmint.core.introspection import ExperimentFunction, ExperimentPath, ExperimentPlan

        func_key = "test:error_func"
        plan = ExperimentPlan(
            functions={
                func_key: ExperimentFunction(
                    key=func_key,
                    name="error_func",
                    file_path=Path("test.py"),
                    lineno=1,
                    is_async=True,
                    branch_strategy=None,
                    config_count=1,
                    config_ids=["err"],
                )
            },
            call_graph={func_key: set()},
            paths=[
                ExperimentPath(
                    path_id="err_path",
                    config_assignments={func_key: "err"},
                    function_order=[func_key],
                )
            ],
            root_key=func_key,
        )

        async def failing_func() -> None:
            raise ValueError("Test error")

        executor = PlanExecutor(plan)
        result = await executor.execute(failing_func)

        assert len(result.path_results) == 1
        assert result.path_results[0].success is False
        assert result.path_results[0].exception is not None
        assert "Test error" in str(result.path_results[0].exception)
