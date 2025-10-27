"""Tests for @experiment decorator."""

import pytest

from spearmint import Spearmint
from spearmint.branch import BranchContainer
from spearmint.strategies import (
    MultiBranchStrategy,
    RoundRobinStrategy,
    ShadowStrategy,
)

mint = Spearmint()


class TestExperimentDecorator:
    """Test @experiment decorator functionality."""

    @pytest.mark.asyncio
    async def test_experiment_decorator_round_robin(self, sample_configs):
        """@experiment with RoundRobinStrategy should work correctly."""

        @mint.experiment(RoundRobinStrategy())
        async def my_func(x: int, config: dict) -> int:
            return x + config["delta"]

        # First call
        mint.configs = sample_configs
        result1 = await my_func(10)
        assert result1 == 11  # 10 + 1

        # Second call
        result2 = await my_func(10)
        assert result2 == 15  # 10 + 5

    @pytest.mark.asyncio
    async def test_experiment_decorator_shadow(self, sample_configs):
        """@experiment with ShadowStrategy should return primary result."""

        @mint.experiment(ShadowStrategy(primary_index=0))
        async def my_func(x: int, config: dict) -> int:
            return x + config["delta"]

        mint.configs = sample_configs
        result = await my_func(10)
        assert result == 11  # Primary config (delta=1)

    @pytest.mark.asyncio
    async def test_experiment_decorator_multi_branch(self, sample_configs):
        """@experiment with MultiBranchStrategy should return BranchContainer."""

        @mint.experiment(MultiBranchStrategy())
        async def my_func(x: int, config: dict) -> int:
            return x + config["delta"]

        mint.configs = sample_configs
        result = await my_func(10)

        assert isinstance(result, BranchContainer)
        assert len(result) == 3
        assert all(b.status == "success" for b in result)

    @pytest.mark.asyncio
    async def test_experiment_with_extra_kwargs(self, sample_configs):
        """@experiment should pass through extra kwargs to function."""

        @mint.experiment(RoundRobinStrategy())
        async def my_func(x: int, y: int, config: dict) -> int:
            return x + y + config["delta"]

        mint.configs = sample_configs
        result = await my_func(10, y=5)
        assert result == 16  # 10 + 5 + 1

    @pytest.mark.asyncio
    async def test_experiment_preserves_function_metadata(self):
        """@experiment should preserve function name and docstring."""

        @mint.experiment(RoundRobinStrategy())
        async def my_special_func(x: int, config: dict) -> int:
            """This is a special function."""
            return x + config["delta"]

        assert my_special_func.__name__ == "my_special_func"
        assert "special function" in my_special_func.__doc__

    @pytest.mark.asyncio
    async def test_experiment_failure_propagation(self, sample_configs):
        """@experiment should propagate exceptions from strategies."""

        @mint.experiment(RoundRobinStrategy())
        async def failing_func(x: int, config: dict) -> int:
            raise ValueError("Test failure")

        with pytest.raises(RuntimeError, match="ValueError: Test failure"):
            mint.configs = sample_configs
            await failing_func(10)
