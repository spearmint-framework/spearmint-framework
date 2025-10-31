"""Tests for strategy implementations."""

import asyncio

import pytest
from pydantic import BaseModel

from spearmint.branch import BranchContainer
from spearmint.config.config import Config
from spearmint.strategies import (
    MultiBranchStrategy,
    RoundRobinStrategy,
    ShadowStrategy,
)
from spearmint.strategies.single_config import SingleConfigStrategy


class TestConfig(BaseModel):
    """Test configuration model."""

    delta: int
    multiplier: int = 1


class NestedConfig(BaseModel):
    """Test configuration with nested structure."""

    value: int


class TestSingleConfigStrategy:
    """Test SingleConfigStrategy execution."""

    @pytest.mark.asyncio
    async def test_single_config_executes_successfully(self):
        """SingleConfigStrategy should execute with one config and return output."""
        configs = [Config({"delta": 5, "multiplier": 2})]
        bindings = {TestConfig: ""}
        strategy = SingleConfigStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            return config.delta * config.multiplier

        result = await strategy.run(func)
        assert result == 10

    @pytest.mark.asyncio
    async def test_single_config_with_args_and_kwargs(self):
        """SingleConfigStrategy should pass through args and kwargs."""
        configs = [Config({"delta": 3, "multiplier": 2})]
        bindings = {TestConfig: ""}
        strategy = SingleConfigStrategy(configs, bindings)

        async def func(x: int, config: TestConfig, y: int = 0) -> int:
            return x + config.delta * config.multiplier + y

        result = await strategy.run(func, 10, y=5)
        assert result == 21  # 10 + (3*2) + 5

    @pytest.mark.asyncio
    async def test_single_config_raises_on_function_failure(self):
        """SingleConfigStrategy should raise RuntimeError when function fails."""
        configs = [Config({"delta": 5, "multiplier": 2})]
        bindings = {TestConfig: ""}
        strategy = SingleConfigStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            raise ValueError("Intentional error")

        with pytest.raises(RuntimeError, match="ValueError: Intentional error"):
            await strategy.run(func)

    @pytest.mark.asyncio
    async def test_single_config_raises_on_empty_configs(self):
        """SingleConfigStrategy should raise ValueError with empty configs."""
        configs = []
        bindings = {TestConfig: ""}
        strategy = SingleConfigStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            return 42

        with pytest.raises(ValueError, match="SingleConfigStrategy requires one config"):
            await strategy.run(func)

    @pytest.mark.asyncio
    async def test_single_config_with_nested_binding(self):
        """SingleConfigStrategy should support nested config bindings."""
        configs = [Config({"nested": {"value": 42}})]
        bindings = {NestedConfig: "nested"}
        strategy = SingleConfigStrategy(configs, bindings)

        async def func(config: NestedConfig) -> int:
            return config.value * 2

        result = await strategy.run(func)
        assert result == 84


class TestRoundRobinStrategy:
    """Test RoundRobinStrategy execution."""

    @pytest.mark.asyncio
    async def test_round_robin_cycles_through_configs(self):
        """RoundRobinStrategy should cycle through configs sequentially."""
        configs = [
            Config({"delta": 1, "multiplier": 1}),
            Config({"delta": 2, "multiplier": 1}),
            Config({"delta": 3, "multiplier": 1}),
        ]
        bindings = {TestConfig: ""}
        strategy = RoundRobinStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            return config.delta

        # First execution
        result1 = await strategy.run(func)
        assert result1 == 1

        # Second execution
        result2 = await strategy.run(func)
        assert result2 == 2

        # Third execution
        result3 = await strategy.run(func)
        assert result3 == 3

        # Should wrap around to first config
        result4 = await strategy.run(func)
        assert result4 == 1

    @pytest.mark.asyncio
    async def test_round_robin_with_single_config(self):
        """RoundRobinStrategy should work with single config."""
        configs = [Config({"delta": 5, "multiplier": 2})]
        bindings = {TestConfig: ""}
        strategy = RoundRobinStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            return config.delta * config.multiplier

        result1 = await strategy.run(func)
        assert result1 == 10

        # Should return to same config
        result2 = await strategy.run(func)
        assert result2 == 10

    @pytest.mark.asyncio
    async def test_round_robin_raises_on_empty_configs(self):
        """RoundRobinStrategy should raise ValueError with empty configs."""
        configs = []
        bindings = {TestConfig: ""}
        strategy = RoundRobinStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            return 42

        with pytest.raises(ValueError, match="RoundRobinStrategy requires at least one config"):
            await strategy.run(func)

    @pytest.mark.asyncio
    async def test_round_robin_raises_on_function_failure(self):
        """RoundRobinStrategy should raise RuntimeError when function fails."""
        configs = [Config({"delta": 1, "multiplier": 1})]
        bindings = {TestConfig: ""}
        strategy = RoundRobinStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            raise ValueError("Test error")

        with pytest.raises(RuntimeError, match="ValueError: Test error"):
            await strategy.run(func)

    @pytest.mark.asyncio
    async def test_round_robin_index_persists_across_calls(self):
        """RoundRobinStrategy index should persist across multiple calls."""
        configs = [
            Config({"delta": 10, "multiplier": 1}),
            Config({"delta": 20, "multiplier": 1}),
        ]
        bindings = {TestConfig: ""}
        strategy = RoundRobinStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            return config.delta

        results = [await strategy.run(func) for _ in range(5)]
        assert results == [10, 20, 10, 20, 10]

    @pytest.mark.asyncio
    async def test_round_robin_with_args_and_kwargs(self):
        """RoundRobinStrategy should pass through args and kwargs."""
        configs = [
            Config({"delta": 1, "multiplier": 2}),
            Config({"delta": 2, "multiplier": 2}),
        ]
        bindings = {TestConfig: ""}
        strategy = RoundRobinStrategy(configs, bindings)

        async def func(x: int, config: TestConfig, y: int = 0) -> int:
            return x + config.delta * config.multiplier + y

        result1 = await strategy.run(func, 100, y=10)
        assert result1 == 112  # 100 + (1*2) + 10

        result2 = await strategy.run(func, 100, y=10)
        assert result2 == 114  # 100 + (2*2) + 10


class TestShadowStrategy:
    """Test ShadowStrategy execution."""

    @pytest.mark.asyncio
    async def test_shadow_executes_primary_immediately(self):
        """ShadowStrategy should execute primary config and return result."""
        configs = [
            Config({"delta": 10, "multiplier": 1}),
            Config({"delta": 20, "multiplier": 1}),
            Config({"delta": 30, "multiplier": 1}),
        ]
        bindings = {TestConfig: ""}
        strategy = ShadowStrategy(configs, bindings, primary_index=0)

        async def func(config: TestConfig) -> int:
            return config.delta

        result = await strategy.run(func)
        assert result == 10

    @pytest.mark.asyncio
    async def test_shadow_schedules_shadow_tasks(self):
        """ShadowStrategy should schedule shadow tasks in background."""
        configs = [
            Config({"delta": 10, "multiplier": 1}),
            Config({"delta": 20, "multiplier": 1}),
            Config({"delta": 30, "multiplier": 1}),
        ]
        bindings = {TestConfig: ""}
        strategy = ShadowStrategy(configs, bindings, primary_index=0)

        async def func(config: TestConfig) -> int:
            await asyncio.sleep(0.01)
            return config.delta

        result = await strategy.run(func)
        assert result == 10

        # Shadow tasks should be created
        assert len(strategy._shadow_tasks) == 2

        # Gather shadow results
        shadow_branches = await strategy.gather_shadows()
        assert len(shadow_branches) == 2
        assert shadow_branches[0].output == 20
        assert shadow_branches[1].output == 30

    @pytest.mark.asyncio
    async def test_shadow_with_different_primary_index(self):
        """ShadowStrategy should respect custom primary_index."""
        configs = [
            Config({"delta": 10, "multiplier": 1}),
            Config({"delta": 20, "multiplier": 1}),
            Config({"delta": 30, "multiplier": 1}),
        ]
        bindings = {TestConfig: ""}
        strategy = ShadowStrategy(configs, bindings, primary_index=1)

        async def func(config: TestConfig) -> int:
            return config.delta

        result = await strategy.run(func)
        assert result == 20

        shadow_branches = await strategy.gather_shadows()
        assert len(shadow_branches) == 2
        assert shadow_branches[0].output == 10
        assert shadow_branches[1].output == 30

    @pytest.mark.asyncio
    async def test_shadow_raises_on_empty_configs(self):
        """ShadowStrategy should raise ValueError with empty configs."""
        configs = []
        bindings = {TestConfig: ""}
        strategy = ShadowStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            return 42

        with pytest.raises(ValueError, match="ShadowStrategy requires at least one config"):
            await strategy.run(func)

    @pytest.mark.asyncio
    async def test_shadow_raises_on_invalid_primary_index(self):
        """ShadowStrategy should raise ValueError with out-of-range primary_index."""
        configs = [Config({"delta": 10, "multiplier": 1})]
        bindings = {TestConfig: ""}
        strategy = ShadowStrategy(configs, bindings, primary_index=5)

        async def func(config: TestConfig) -> int:
            return 42

        with pytest.raises(ValueError, match="Primary index 5 out of range"):
            await strategy.run(func)

    @pytest.mark.asyncio
    async def test_shadow_raises_on_primary_failure(self):
        """ShadowStrategy should raise RuntimeError when primary fails."""
        configs = [
            Config({"delta": 10, "multiplier": 1}),
            Config({"delta": 20, "multiplier": 1}),
        ]
        bindings = {TestConfig: ""}
        strategy = ShadowStrategy(configs, bindings, primary_index=0)

        async def func(config: TestConfig) -> int:
            if config.delta == 10:
                raise ValueError("Primary failure")
            return config.delta

        with pytest.raises(RuntimeError, match="ValueError: Primary failure"):
            await strategy.run(func)

    @pytest.mark.asyncio
    async def test_shadow_continues_shadows_on_primary_success(self):
        """ShadowStrategy should execute shadows even if primary succeeds."""
        configs = [
            Config({"delta": 10, "multiplier": 1}),
            Config({"delta": 20, "multiplier": 1}),
        ]
        bindings = {TestConfig: ""}
        strategy = ShadowStrategy(configs, bindings, primary_index=0)

        execution_order = []

        async def func(config: TestConfig) -> int:
            execution_order.append(config.delta)
            await asyncio.sleep(0.01)
            return config.delta

        result = await strategy.run(func)
        assert result == 10
        assert len(execution_order) == 1  # Only primary executed synchronously

        # Wait for shadows
        shadow_branches = await strategy.gather_shadows()
        assert len(shadow_branches) == 1
        assert len(execution_order) == 2  # Shadow also executed

    @pytest.mark.asyncio
    async def test_shadow_gather_shadows_returns_empty_for_single_config(self):
        """ShadowStrategy.gather_shadows should return empty list for single config."""
        configs = [Config({"delta": 10, "multiplier": 1})]
        bindings = {TestConfig: ""}
        strategy = ShadowStrategy(configs, bindings, primary_index=0)

        async def func(config: TestConfig) -> int:
            return config.delta

        await strategy.run(func)
        shadow_branches = await strategy.gather_shadows()
        assert shadow_branches == []

    @pytest.mark.asyncio
    async def test_shadow_with_args_and_kwargs(self):
        """ShadowStrategy should pass through args and kwargs."""
        configs = [
            Config({"delta": 1, "multiplier": 2}),
            Config({"delta": 2, "multiplier": 2}),
        ]
        bindings = {TestConfig: ""}
        strategy = ShadowStrategy(configs, bindings, primary_index=0)

        async def func(x: int, config: TestConfig, y: int = 0) -> int:
            return x + config.delta * config.multiplier + y

        result = await strategy.run(func, 100, y=10)
        assert result == 112  # 100 + (1*2) + 10


class TestMultiBranchStrategy:
    """Test MultiBranchStrategy execution."""

    @pytest.mark.asyncio
    async def test_multi_branch_executes_all_configs(self):
        """MultiBranchStrategy should execute all configs concurrently."""
        configs = [
            Config({"delta": 1, "multiplier": 2}),
            Config({"delta": 2, "multiplier": 3}),
            Config({"delta": 3, "multiplier": 4}),
        ]
        bindings = {TestConfig: ""}
        strategy = MultiBranchStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            await asyncio.sleep(0.01)
            return config.delta * config.multiplier

        result = await strategy.run(func)

        assert isinstance(result, BranchContainer)
        assert len(result) == 3
        assert result[0].output == 2
        assert result[1].output == 6
        assert result[2].output == 12

    @pytest.mark.asyncio
    async def test_multi_branch_returns_branch_container(self):
        """MultiBranchStrategy should return BranchContainer with all branches."""
        configs = [
            Config({"delta": 10, "multiplier": 1}),
            Config({"delta": 20, "multiplier": 1}),
        ]
        bindings = {TestConfig: ""}
        strategy = MultiBranchStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            return config.delta

        result = await strategy.run(func)

        assert isinstance(result, BranchContainer)
        assert len(result) == 2
        assert all(branch.status == "success" for branch in result)

    @pytest.mark.asyncio
    async def test_multi_branch_handles_partial_failures(self):
        """MultiBranchStrategy should capture failures in individual branches."""
        configs = [
            Config({"delta": 1, "multiplier": 1}),
            Config({"delta": 2, "multiplier": 1}),
            Config({"delta": 3, "multiplier": 1}),
        ]
        bindings = {TestConfig: ""}
        strategy = MultiBranchStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            if config.delta == 2:
                raise ValueError("Intentional failure")
            return config.delta * 10

        result = await strategy.run(func)

        assert len(result) == 3
        assert result[0].status == "success"
        assert result[0].output == 10
        assert result[1].status == "failed"
        assert result[1].exception_info is not None
        assert "ValueError" in result[1].exception_info["type"]
        assert result[2].status == "success"
        assert result[2].output == 30

    @pytest.mark.asyncio
    async def test_multi_branch_successful_filtering(self):
        """MultiBranchStrategy results should support successful() filtering."""
        configs = [
            Config({"delta": 1, "multiplier": 1}),
            Config({"delta": 2, "multiplier": 1}),
            Config({"delta": 3, "multiplier": 1}),
        ]
        bindings = {TestConfig: ""}
        strategy = MultiBranchStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            if config.delta == 2:
                raise ValueError("Fail")
            return config.delta

        result = await strategy.run(func)
        successful = result.successful()

        assert len(successful) == 2
        assert successful[0].output == 1
        assert successful[1].output == 3

    @pytest.mark.asyncio
    async def test_multi_branch_failed_filtering(self):
        """MultiBranchStrategy results should support failed() filtering."""
        configs = [
            Config({"delta": 1, "multiplier": 1}),
            Config({"delta": 2, "multiplier": 1}),
            Config({"delta": 3, "multiplier": 1}),
        ]
        bindings = {TestConfig: ""}
        strategy = MultiBranchStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            if config.delta == 2:
                raise ValueError("Fail")
            return config.delta

        result = await strategy.run(func)
        failed = result.failed()

        assert len(failed) == 1
        assert failed[0].exception_info is not None
        assert "ValueError" in failed[0].exception_info["type"]

    @pytest.mark.asyncio
    async def test_multi_branch_raises_on_empty_configs(self):
        """MultiBranchStrategy should raise ValueError with empty configs."""
        configs = []
        bindings = {TestConfig: ""}
        strategy = MultiBranchStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            return 42

        with pytest.raises(ValueError, match="MultiBranchStrategy requires at least one config"):
            await strategy.run(func)

    @pytest.mark.asyncio
    async def test_multi_branch_with_args_and_kwargs(self):
        """MultiBranchStrategy should pass through args and kwargs to all branches."""
        configs = [
            Config({"delta": 1, "multiplier": 2}),
            Config({"delta": 2, "multiplier": 2}),
        ]
        bindings = {TestConfig: ""}
        strategy = MultiBranchStrategy(configs, bindings)

        async def func(x: int, config: TestConfig, y: int = 0) -> int:
            return x + config.delta * config.multiplier + y

        result = await strategy.run(func, 100, y=10)

        assert len(result) == 2
        assert result[0].output == 112  # 100 + (1*2) + 10
        assert result[1].output == 114  # 100 + (2*2) + 10

    @pytest.mark.asyncio
    async def test_multi_branch_by_config_id(self):
        """MultiBranchStrategy results should support by_config_id() lookup."""
        configs = [
            Config({"config_id": "test1", "delta": 1, "multiplier": 1}),
            Config({"config_id": "test2", "delta": 2, "multiplier": 1}),
        ]
        bindings = {TestConfig: ""}
        strategy = MultiBranchStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            return config.delta * 10

        result = await strategy.run(func)

        branch = result.by_config_id("test2")
        assert branch is not None
        assert branch.output == 20

    @pytest.mark.asyncio
    async def test_multi_branch_concurrent_execution(self):
        """MultiBranchStrategy should execute branches concurrently."""
        configs = [Config({"delta": i, "multiplier": 1}) for i in range(5)]
        bindings = {TestConfig: ""}
        strategy = MultiBranchStrategy(configs, bindings)

        execution_times = []

        async def func(config: TestConfig) -> int:
            import time

            start = time.perf_counter()
            await asyncio.sleep(0.1)
            execution_times.append(time.perf_counter() - start)
            return config.delta

        import time

        overall_start = time.perf_counter()
        result = await strategy.run(func)
        overall_duration = time.perf_counter() - overall_start

        # If executed concurrently, overall time should be ~0.1s not ~0.5s
        assert len(result) == 5
        assert overall_duration < 0.3  # Allow some overhead, but much less than sequential


class TestStrategyConfigBinding:
    """Test config binding functionality across strategies."""

    @pytest.mark.asyncio
    async def test_nested_config_binding(self):
        """Strategies should support nested config path bindings."""
        configs = [
            Config({"app": {"nested": {"value": 42}}}),
        ]
        bindings = {NestedConfig: "app.nested"}
        strategy = SingleConfigStrategy(configs, bindings)

        async def func(config: NestedConfig) -> int:
            return config.value * 2

        result = await strategy.run(func)
        assert result == 84

    @pytest.mark.asyncio
    async def test_multiple_config_models(self):
        """Strategies should support multiple config model bindings."""

        class ConfigA(BaseModel):
            value_a: int

        class ConfigB(BaseModel):
            value_b: int

        configs = [
            Config({"section_a": {"value_a": 10}, "section_b": {"value_b": 20}}),
        ]
        bindings = {ConfigA: "section_a", ConfigB: "section_b"}
        strategy = SingleConfigStrategy(configs, bindings)

        async def func(config_a: ConfigA, config_b: ConfigB) -> int:
            return config_a.value_a + config_b.value_b

        result = await strategy.run(func)
        assert result == 30

    @pytest.mark.asyncio
    async def test_invalid_binding_path_raises_error(self):
        """Strategies should raise ValueError for invalid binding paths."""
        configs = [Config({"delta": 10, "multiplier": 1})]
        bindings = {NestedConfig: "nonexistent.path"}
        strategy = SingleConfigStrategy(configs, bindings)

        async def func(config: NestedConfig) -> int:
            return config.value

        with pytest.raises(ValueError, match="Key 'nonexistent' not found"):
            await strategy.run(func)


class TestStrategyConfigIdGeneration:
    """Test config ID generation across strategies."""

    @pytest.mark.asyncio
    async def test_config_id_from_explicit_field(self):
        """Strategies should use explicit config_id if provided."""
        configs = [
            Config({"config_id": "custom-id", "delta": 10, "multiplier": 1}),
        ]
        bindings = {TestConfig: ""}
        strategy = MultiBranchStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            return config.delta

        result = await strategy.run(func)
        assert result[0].config_id == "custom-id"

    @pytest.mark.asyncio
    async def test_config_id_generated_from_hash(self):
        """Strategies should generate hash-based config_id if not provided."""
        configs = [
            Config({"delta": 10, "multiplier": 1}),
        ]
        bindings = {TestConfig: ""}
        strategy = MultiBranchStrategy(configs, bindings)

        async def func(config: TestConfig) -> int:
            return config.delta

        result = await strategy.run(func)
        # Should be a 16-character hex string
        assert len(result[0].config_id) == 16
        assert all(c in "0123456789abcdef" for c in result[0].config_id)

    @pytest.mark.asyncio
    async def test_identical_configs_generate_same_id(self):
        """Identical configs should generate the same config_id."""
        config1 = Config({"delta": 10, "multiplier": 1})
        config2 = Config({"delta": 10, "multiplier": 1})

        bindings = {TestConfig: ""}
        strategy1 = SingleConfigStrategy([config1], bindings)
        strategy2 = SingleConfigStrategy([config2], bindings)

        async def func(config: TestConfig) -> int:
            return config.delta

        # Access the generated config IDs
        id1 = strategy1.config_ids[0]
        id2 = strategy2.config_ids[0]

        assert id1 == id2
