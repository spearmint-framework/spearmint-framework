"""Tests for @experiment decorator."""

import pytest

from spearmint.branch import BranchContainer
from spearmint.experiment import experiment
from spearmint.strategies import (
    MultiBranchStrategy,
    RoundRobinStrategy,
    ShadowStrategy,
)


class TestExperimentDecorator:
    """Test @experiment decorator functionality."""

    @pytest.mark.asyncio
    async def test_experiment_decorator_round_robin(self, sample_configs):
        """@experiment with RoundRobinStrategy should work correctly."""

        @experiment(RoundRobinStrategy())
        async def my_func(x: int, config: dict) -> int:
            return x + config["delta"]

        # First call
        result1 = await my_func(10, configs=sample_configs)
        assert result1 == 11  # 10 + 1

        # Second call
        result2 = await my_func(10, configs=sample_configs)
        assert result2 == 15  # 10 + 5

    @pytest.mark.asyncio
    async def test_experiment_decorator_shadow(self, sample_configs):
        """@experiment with ShadowStrategy should return primary result."""

        @experiment(ShadowStrategy(primary_index=0))
        async def my_func(x: int, config: dict) -> int:
            return x + config["delta"]

        result = await my_func(10, configs=sample_configs)
        assert result == 11  # Primary config (delta=1)

    @pytest.mark.asyncio
    async def test_experiment_decorator_multi_branch(self, sample_configs):
        """@experiment with MultiBranchStrategy should return BranchContainer."""

        @experiment(MultiBranchStrategy())
        async def my_func(x: int, config: dict) -> int:
            return x + config["delta"]

        result = await my_func(10, configs=sample_configs)

        assert isinstance(result, BranchContainer)
        assert len(result) == 3
        assert all(b.status == "success" for b in result)

    @pytest.mark.asyncio
    async def test_experiment_requires_configs(self):
        """@experiment should raise ValueError if configs not provided."""

        @experiment(RoundRobinStrategy())
        async def my_func(x: int, config: dict) -> int:
            return x + config["delta"]

        with pytest.raises(ValueError, match="requires 'configs' keyword argument"):
            await my_func(10)

    @pytest.mark.asyncio
    async def test_experiment_with_logger(self, sample_configs, in_memory_logger):
        """@experiment should pass logger to strategy."""

        @experiment(RoundRobinStrategy())
        async def my_func(x: int, config: dict) -> int:
            return x + config["delta"]

        result = await my_func(10, configs=sample_configs, logger=in_memory_logger)
        assert result == 11

        # Verify logging occurred
        assert in_memory_logger.get_run_count() == 1
        assert in_memory_logger.get_branch_count() == 1

    @pytest.mark.asyncio
    async def test_experiment_with_extra_kwargs(self, sample_configs):
        """@experiment should pass through extra kwargs to function."""

        @experiment(RoundRobinStrategy())
        async def my_func(x: int, y: int, config: dict) -> int:
            return x + y + config["delta"]

        result = await my_func(10, y=5, configs=sample_configs)
        assert result == 16  # 10 + 5 + 1

    @pytest.mark.asyncio
    async def test_experiment_preserves_function_metadata(self):
        """@experiment should preserve function name and docstring."""

        @experiment(RoundRobinStrategy())
        async def my_special_func(x: int, config: dict) -> int:
            """This is a special function."""
            return x + config["delta"]

        assert my_special_func.__name__ == "my_special_func"
        assert "special function" in my_special_func.__doc__

    def test_experiment_requires_async_function(self):
        """@experiment should raise TypeError for non-async functions."""

        with pytest.raises(TypeError, match="must be async"):

            @experiment(RoundRobinStrategy())
            def sync_func(x: int, config: dict) -> int:
                return x + config["delta"]

    @pytest.mark.asyncio
    async def test_experiment_failure_propagation(self, sample_configs):
        """@experiment should propagate exceptions from strategies."""

        @experiment(RoundRobinStrategy())
        async def failing_func(x: int, config: dict) -> int:
            raise ValueError("Test failure")

        with pytest.raises(RuntimeError, match="ValueError: Test failure"):
            await failing_func(10, configs=sample_configs)
