"""Tests for strategy registration API."""

import pytest

from spearmint.registry import get_strategy, list_strategies, register_strategy
from spearmint.strategies import (
    MultiBranchStrategy,
    RoundRobinStrategy,
    ShadowStrategy,
)


class TestStrategyRegistration:
    """Test strategy registration and lookup."""

    def test_list_builtin_strategies(self):
        """list_strategies should include built-in strategies."""
        strategies = list_strategies()

        assert "round_robin" in strategies
        assert "shadow" in strategies
        assert "multi_branch" in strategies

    def test_get_builtin_strategy(self):
        """get_strategy should return instances of built-in strategies."""
        rr = get_strategy("round_robin")
        assert isinstance(rr, RoundRobinStrategy)

        shadow = get_strategy("shadow")
        assert isinstance(shadow, ShadowStrategy)

        multi = get_strategy("multi_branch")
        assert isinstance(multi, MultiBranchStrategy)

    def test_get_strategy_creates_new_instance(self):
        """get_strategy should create new instances each time."""
        rr1 = get_strategy("round_robin")
        rr2 = get_strategy("round_robin")

        assert rr1 is not rr2

    def test_get_unknown_strategy_raises(self):
        """get_strategy should raise ValueError for unknown strategy."""
        with pytest.raises(ValueError, match="Unknown strategy 'nonexistent'"):
            get_strategy("nonexistent")

    def test_register_custom_strategy(self):
        """register_strategy should allow registering custom strategies."""

        class CustomStrategy:
            async def run(self, func, configs, *args, **kwargs):
                return "custom"

        register_strategy("custom", CustomStrategy)

        # Should be retrievable
        strategy = get_strategy("custom")
        assert isinstance(strategy, CustomStrategy)

        # Should appear in list
        assert "custom" in list_strategies()

    def test_register_duplicate_raises(self):
        """Registering duplicate strategy name should raise ValueError."""

        class DuplicateStrategy:
            async def run(self, func, configs, *args, **kwargs):
                return "duplicate"

        register_strategy("duplicate_test", DuplicateStrategy)

        with pytest.raises(ValueError, match="already registered"):
            register_strategy("duplicate_test", DuplicateStrategy)
